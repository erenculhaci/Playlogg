# Place this file in your common app: common/storage.py
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    """
    Custom storage for handling media files with S3.
    """
    location = 'media'  # This creates a 'media' folder in your bucket root
    file_overwrite = settings.AWS_S3_FILE_OVERWRITE
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME

    def url(self, name, parameters=None, expire=None):
        """
        Override the URL method to handle the 'media/' prefix correctly.
        """
        url = super().url(name, parameters, expire)
        # Return the URL if it's valid
        if url:
            return url
        # Default fallback
        return f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{self.location}/{name}"

    def get_available_name(self, name, max_length=None):
        """
        Returns a filename that's free on the target storage system.
        """
        # If the filename already exists, add a suffix
        name = super().get_available_name(name, max_length)
        return name


class StaticStorage(S3Boto3Storage):
    """
    Custom storage for static files on S3.
    """
    location = 'static'
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME