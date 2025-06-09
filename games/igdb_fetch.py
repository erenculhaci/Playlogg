import requests
import os
from datetime import datetime
from django.conf import settings
from django.core.files.base import ContentFile
from .models import Game
from django.contrib.auth import get_user_model
import boto3
from botocore.exceptions import ClientError

# IGDB API Credentials
TWITCH_CLIENT_ID = settings.TWITCH_CLIENT_ID
TWITCH_CLIENT_SECRET = settings.TWITCH_CLIENT_SECRET


# Get OAuth Token
def get_igdb_token():
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": TWITCH_CLIENT_ID,
        "client_secret": TWITCH_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    response = requests.post(url, params=params)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch IGDB token: {response.json()}")

    return response.json()["access_token"]


# Convert Unix timestamp to YYYY-MM-DD date
def unix_to_date(timestamp):
    return datetime.utcfromtimestamp(timestamp).date() if timestamp else None


def sanitize_filename(filename):
    """
    Remove invalid characters from filenames for Windows compatibility.
    """
    # Replace characters that are invalid in Windows filenames
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')

    # Also remove any leading/trailing spaces or dots which can cause issues
    filename = filename.strip('. ')

    # Ensure the filename isn't empty after sanitization
    if not filename:
        filename = "unnamed_file"

    return filename


def upload_image_to_s3(image_content, image_name):
    """
    Upload image content directly to S3 bucket.

    Args:
        image_content (bytes): Image content as bytes
        image_name (str): Name for the image file

    Returns:
        str: S3 key path if successful, None if failed
    """
    try:
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )

        # Create the S3 key path
        s3_key = f"media/game_images/{image_name}"

        # Upload the image
        s3_client.put_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=s3_key,
            Body=image_content,
            ContentType='image/jpeg',
            CacheControl='max-age=86400'
        )

        print(f"Successfully uploaded image to S3: {s3_key}")
        return f"game_images/{image_name}"  # Return the path as stored in the model

    except ClientError as e:
        print(f"Error uploading image to S3: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error uploading image: {e}")
        return None


def check_image_exists_in_s3(image_name):
    """
    Check if an image already exists in S3 bucket.

    Args:
        image_name (str): Name of the image file

    Returns:
        bool: True if image exists, False otherwise
    """
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )

        s3_key = f"media/game_images/{image_name}"
        s3_client.head_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=s3_key)
        return True
    except ClientError:
        return False
    except Exception as e:
        print(f"Error checking image existence: {e}")
        return False


# Fetch all games from IGDB in batches
def fetch_all_games_from_igdb():
    User = get_user_model()
    system_user, _ = User.objects.get_or_create(username="IGDB_Bot", defaults={"is_staff": True})
    token = get_igdb_token()
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {token}"
    }

    offset = 0
    limit = 500  # IGDB allows a max of 500
    total_games_added = 0

    while True:
        query = f"""
            fields name, summary, first_release_date, genres.name, platforms.name, 
            involved_companies.company.name, cover.url;
            sort first_release_date desc;
            limit {limit};
            offset {offset};
        """

        url = "https://api.igdb.com/v4/games"
        response = requests.post(url, headers=headers, data=query)

        if response.status_code != 200:
            print(f"Error fetching IGDB data: {response.status_code}, {response.text}")
            break

        games = response.json()
        if not games:
            break  # Stop when no more games are returned

        for data in games:
            name = data.get("name")
            if not name:
                continue  # Skip if no name exists

            description = data.get("summary", "")
            release_date = unix_to_date(data.get("first_release_date"))
            studio = data.get("involved_companies", [{}])[0].get("company", {}).get("name", "Unknown Studio")
            genres = [genre["name"] for genre in data.get("genres", [])]
            platforms = [platform["name"] for platform in data.get("platforms", [])]

            # Handle image downloading and uploading to S3
            image_path = None
            image_url = data.get("cover", {}).get("url", None)

            if image_url:
                # Ensure the URL is properly formatted
                if not image_url.startswith('http'):
                    image_url = f"https:{image_url}"

                # Get higher quality image
                image_url = image_url.replace('t_thumb', 't_cover_big')

                # Create sanitized filename
                image_name = sanitize_filename(f"{name.replace(' ', '_').replace('/', '_').lower()}.jpg")

                # Check if image already exists in S3 to avoid duplicate uploads
                if not check_image_exists_in_s3(image_name):
                    try:
                        # Download the image
                        image_response = requests.get(image_url, timeout=30)
                        if image_response.status_code == 200:
                            # Upload directly to S3
                            image_path = upload_image_to_s3(image_response.content, image_name)
                            if image_path:
                                print(f"Successfully processed image for {name}")
                            else:
                                print(f"Failed to upload image for {name}")
                        else:
                            print(f"Failed to download image for {name}: {image_response.status_code}")
                    except requests.exceptions.RequestException as e:
                        print(f"Error downloading image for {name}: {e}")
                    except Exception as e:
                        print(f"Unexpected error processing image for {name}: {e}")
                else:
                    # Image already exists, use existing path
                    image_path = f"game_images/{image_name}"
                    print(f"Image already exists for {name}")

            try:
                # Save game in the database
                game, created = Game.objects.get_or_create(
                    name=name,
                    defaults={
                        "description": description,
                        "release_date": release_date,
                        "studio": studio,
                        "genres": genres,
                        "platforms": platforms,
                        "image": image_path if image_path else "game_images/default_game.jpg",
                        "added_by": system_user
                    }
                )

                # If game exists but doesn't have an image, update it
                if not created and not game.image and image_path:
                    game.image = image_path
                    game.save()
                    print(f"Updated existing game {name} with new image")

            except Exception as e:
                print(f"Error saving game {name}: {e}")
                print(f"Data: {data}")
                continue

            if created:
                total_games_added += 1

        print(f"Fetched {len(games)} games, total added: {total_games_added}")

        offset += limit  # Move to the next batch

    print(f"✅ Finished! Total new games added: {total_games_added}")
    return total_games_added


import requests
import os
from datetime import datetime
from django.conf import settings
from django.core.files.base import ContentFile
from .models import Game
from django.contrib.auth import get_user_model
import boto3
from botocore.exceptions import ClientError

# IGDB API Credentials
TWITCH_CLIENT_ID = settings.TWITCH_CLIENT_ID
TWITCH_CLIENT_SECRET = settings.TWITCH_CLIENT_SECRET


# Get OAuth Token
def get_igdb_token():
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": TWITCH_CLIENT_ID,
        "client_secret": TWITCH_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    response = requests.post(url, params=params)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch IGDB token: {response.json()}")

    return response.json()["access_token"]


# Convert Unix timestamp to YYYY-MM-DD date
def unix_to_date(timestamp):
    return datetime.utcfromtimestamp(timestamp).date() if timestamp else None


def sanitize_filename(filename):
    """
    Remove invalid characters from filenames for Windows compatibility.
    """
    # Replace characters that are invalid in Windows filenames
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')

    # Also remove any leading/trailing spaces or dots which can cause issues
    filename = filename.strip('. ')

    # Ensure the filename isn't empty after sanitization
    if not filename:
        filename = "unnamed_file"

    return filename


def upload_image_to_s3(image_content, image_name):
    """
    Upload image content directly to S3 bucket.

    Args:
        image_content (bytes): Image content as bytes
        image_name (str): Name for the image file

    Returns:
        str: S3 key path if successful, None if failed
    """
    try:
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )

        # Create the S3 key path
        s3_key = f"media/game_images/{image_name}"

        # Upload the image
        s3_client.put_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=s3_key,
            Body=image_content,
            ContentType='image/jpeg',
            CacheControl='max-age=86400'
        )

        print(f"Successfully uploaded image to S3: {s3_key}")
        return f"game_images/{image_name}"  # Return the path as stored in the model

    except ClientError as e:
        print(f"Error uploading image to S3: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error uploading image: {e}")
        return None


def check_image_exists_in_s3(image_name):
    """
    Check if an image already exists in S3 bucket.

    Args:
        image_name (str): Name of the image file

    Returns:
        bool: True if image exists, False otherwise
    """
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )

        s3_key = f"media/game_images/{image_name}"
        s3_client.head_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=s3_key)
        return True
    except ClientError:
        return False
    except Exception as e:
        print(f"Error checking image existence: {e}")
        return False


# Fetch games from IGDB sorted by popularity in batches
def fetch_games_by_popularity():
    User = get_user_model()
    system_user, _ = User.objects.get_or_create(username="IGDB_Bot", defaults={"is_staff": True})
    token = get_igdb_token()
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {token}"
    }

    offset = 0
    limit = 500  # IGDB allows a max of 500
    total_games_added = 0

    while True:
        # Query games sorted by popularity using total_rating_count
        # This sorts by the number of ratings a game has received (popularity indicator)
        query = f"""
            fields name, summary, first_release_date, genres.name, platforms.name, 
            involved_companies.company.name, cover.url, total_rating, total_rating_count;
            where total_rating_count > 10;
            sort total_rating_count desc;
            limit {limit};
            offset {offset};
        """

        url = "https://api.igdb.com/v4/games"
        response = requests.post(url, headers=headers, data=query)

        if response.status_code != 200:
            print(f"Error fetching IGDB data: {response.status_code}, {response.text}")
            break

        games = response.json()
        if not games:
            break  # Stop when no more games are returned

        print(f"Processing batch {offset // limit + 1}: {len(games)} games")

        for data in games:
            name = data.get("name")
            if not name:
                continue  # Skip if no name exists

            description = data.get("summary", "")
            release_date = unix_to_date(data.get("first_release_date"))
            studio = data.get("involved_companies", [{}])[0].get("company", {}).get("name", "Unknown Studio")
            genres = [genre["name"] for genre in data.get("genres", [])]
            platforms = [platform["name"] for platform in data.get("platforms", [])]

            # Get popularity metrics for debugging
            total_rating = data.get("total_rating", 0)
            total_rating_count = data.get("total_rating_count", 0)

            # Handle image downloading and uploading to S3
            image_path = None
            image_url = data.get("cover", {}).get("url", None)

            if image_url:
                # Ensure the URL is properly formatted
                if not image_url.startswith('http'):
                    image_url = f"https:{image_url}"

                # Get higher quality image
                image_url = image_url.replace('t_thumb', 't_cover_big')

                # Create sanitized filename
                image_name = sanitize_filename(f"{name.replace(' ', '_').replace('/', '_').lower()}.jpg")

                # Check if image already exists in S3 to avoid duplicate uploads
                if not check_image_exists_in_s3(image_name):
                    try:
                        # Download the image
                        image_response = requests.get(image_url, timeout=30)
                        if image_response.status_code == 200:
                            # Upload directly to S3
                            image_path = upload_image_to_s3(image_response.content, image_name)
                            if image_path:
                                print(f"Successfully processed image for {name}")
                            else:
                                print(f"Failed to upload image for {name}")
                        else:
                            print(f"Failed to download image for {name}: {image_response.status_code}")
                    except requests.exceptions.RequestException as e:
                        print(f"Error downloading image for {name}: {e}")
                    except Exception as e:
                        print(f"Unexpected error processing image for {name}: {e}")
                else:
                    # Image already exists, use existing path
                    image_path = f"game_images/{image_name}"

            try:
                # Save game in the database
                game, created = Game.objects.get_or_create(
                    name=name,
                    defaults={
                        "description": description,
                        "release_date": release_date,
                        "studio": studio,
                        "genres": genres,
                        "platforms": platforms,
                        "image": image_path if image_path else "game_images/default_game.jpg",
                        "added_by": system_user
                    }
                )

                # If game exists but doesn't have an image, update it
                if not created and not game.image and image_path:
                    game.image = image_path
                    game.save()
                    print(f"Updated existing game {name} with new image")

                if created:
                    total_games_added += 1
                    print(f"Added: {name} (Rating: {total_rating:.1f}, Count: {total_rating_count})")

            except Exception as e:
                print(f"Error saving game {name}: {e}")
                print(f"Data: {data}")
                continue

        print(
            f"Batch {offset // limit + 1} completed. Games in batch: {len(games)}, Total new games added: {total_games_added}")

        offset += limit  # Move to the next batch

        # Optional: Add a small delay to be respectful to the API
        # import time
        # time.sleep(0.1)

    print(f"✅ Finished! Total new games added: {total_games_added}")
    return total_games_added