import boto3
from django.conf import settings


def delete_s3_image(image_path):
    """
    Utility function to delete an image from S3 bucket.

    Args:
        image_path (str): Path to the image file in the bucket

    Returns:
        bool: True if deletion was successful, False otherwise
    """
    if not image_path or image_path.endswith('default_game.jpg') or image_path.endswith('default_profile.jpg'):
        # Don't delete default images
        return False

    try:
        # Initialize S3 client
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )

        # Delete the object from S3
        s3.delete_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=f"media/{image_path}"
        )
        print(f"Deleted S3 image: media/{image_path}")
        return True
    except Exception as e:
        print(f"Error deleting image from S3: {e}")
        return False