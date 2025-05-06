from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils.crypto import get_random_string
from django.conf import settings
import boto3
from common.storage import MediaStorage


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    favorite_games = models.ManyToManyField('games.Game', related_name="favorites", blank=True)

    # Use S3 storage for profile pictures
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        null=True,
        blank=True,
        default='profile_pictures/default_profile.jpg',
        storage=MediaStorage()  # Explicitly use the S3 storage
    )

    is_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=100, blank=True)

    # Track original image for change detection
    _original_image = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Store the original image value to track changes
        self._original_image = self.profile_picture.name if self.profile_picture else None

    def __str__(self):
        return self.user.username

    @property
    def profile_picture_url(self):
        if self.profile_picture and hasattr(self.profile_picture, 'url'):
            return self.profile_picture.url
        else:
            default_url = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/media/profile_pictures/default_profile.jpg"
            return default_url

    def generate_verification_token(self):
        self.verification_token = get_random_string(64)
        self.save()
        return self.verification_token

    def save(self, *args, **kwargs):
        # If no profile picture is provided, set the default image
        if not self.profile_picture:
            self.profile_picture = 'profile_pictures/default_profile.jpg'

        super().save(*args, **kwargs)

        # Update the original image after save
        self._original_image = self.profile_picture.name if self.profile_picture else None


# Signal to create profile when user is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(
            user=instance,
            verification_token=get_random_string(64)
        )


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


# Track the original image before saving to handle replaced images
@receiver(pre_save, sender=Profile)
def track_old_profile_image(sender, instance, **kwargs):
    if instance.id:
        # If this is an update (not a new instance)
        try:
            old_instance = Profile.objects.get(id=instance.id)
            # If the image has changed and there was an old image
            if old_instance.profile_picture and old_instance.profile_picture.name != instance.profile_picture.name:
                if old_instance.profile_picture.name != 'profile_pictures/default_profile.jpg':
                    # Store the old image name to delete later
                    instance._old_image_name = old_instance.profile_picture.name
        except Profile.DoesNotExist:
            pass


# Signal to handle when an image is deleted
@receiver(post_delete, sender=Profile)
def delete_profile_image(sender, instance, **kwargs):
    """
    Delete the image file from S3 when the Profile instance is deleted,
    unless it's the default image.
    """
    if instance.profile_picture and instance.profile_picture.name != 'profile_pictures/default_profile.jpg':
        try:
            # Initialize S3 client
            s3 = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME
            )

            # The key doesn't need the media prefix since it's already in the name
            s3.delete_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=f"media/{instance.profile_picture.name}"
            )
            print(f"Deleted S3 profile image: media/{instance.profile_picture.name}")
        except Exception as e:
            print(f"Error deleting profile image from S3: {e}")