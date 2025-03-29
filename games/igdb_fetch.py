import requests
import os
from datetime import datetime
from django.conf import settings
from .models import Game
from django.contrib.auth import get_user_model

# IGDB API Credentials
TWITCH_CLIENT_ID = "69dpy73ft41u9y3mxgmj18ax77jtnh"
TWITCH_CLIENT_SECRET = "21rwqykrpdi4g5amb8osxswye4ut4p"


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
    limit = 500  # IGDB allows a max of 500, but 50 is safer
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

            # Handle image downloading
            image_url = data.get("cover", {}).get("url", None)
            image_path = None
            if image_url:
                image_url = f"https:{image_url.replace('t_thumb', 't_cover_big')}"  # Ensure valid URL
                image_response = requests.get(image_url)
                if image_response.status_code == 200:
                    image_name = sanitize_filename(f"{name.replace(' ', '_').replace('/', '_').lower()}.jpg")
                    image_path = f"game_images/{image_name}"
                    full_path = os.path.join(settings.MEDIA_ROOT, image_path)
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    with open(full_path, "wb") as img_file:
                        img_file.write(image_response.content)

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
