from django.db import models
from django.contrib.auth.models import User
from django.db.models import JSONField
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from django.db import migrations
from django.conf import settings
import boto3
from common.storage import MediaStorage


class Game(models.Model):
    name = models.CharField(max_length=300)
    description = models.TextField()
    release_date = models.DateField()
    studio = models.CharField(max_length=300)  # Developer or studio
    genres = JSONField(default=list, blank=True)  # List of genres
    platforms = JSONField(default=list, blank=True)  # List of platforms
    likes = models.IntegerField(default=0)
    liked_by = models.ManyToManyField(User, related_name='liked_games', blank=True)
    added_by = models.ForeignKey(User, on_delete=models.CASCADE)

    # Use this approach for tracking image changes
    _original_image = None

    # S3 storage for images - explicitly use MediaStorage
    image = models.ImageField(
        upload_to='game_images/',
        null=True,
        blank=True,
        default='game_images/default_game.jpg',
        storage=MediaStorage()  # Explicitly use the S3 storage
    )

    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['release_date']),
            models.Index(fields=['studio']),
            models.Index(fields=['-id']),
        ]

    class Migration(migrations.Migration):
        dependencies = [
            ('games', 'previous_migration'),
        ]

        operations = [
            migrations.RunSQL(
                'CREATE INDEX games_game_genres_gin ON games_game USING GIN (genres);'
            ),
            migrations.RunSQL(
                'CREATE INDEX games_game_platforms_gin ON games_game USING GIN (platforms);'
            ),
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Store the original image value to track changes
        self._original_image = self.image.name if self.image else None

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # If no image is provided, set the default image
        if not self.image:
            self.image = 'game_images/default_game.jpg'

        # Print debug info
        print(f"Saving game {self.name} with image {self.image}")

        super().save(*args, **kwargs)

        # Update the original image after save
        self._original_image = self.image.name if self.image else None

    @property
    def image_url(self):
        if self.image and hasattr(self.image, 'url'):
            print(f"Image URL: {self.image.url}")
            return self.image.url
        else:
            default_url = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/media/game_images/default_game.jpg"
            print(f"Default URL: {default_url}")
            return default_url


# Track the original image before saving to handle replaced images
@receiver(pre_save, sender=Game)
def track_old_image(sender, instance, **kwargs):
    if instance.id:
        # If this is an update (not a new instance)
        try:
            old_instance = Game.objects.get(id=instance.id)
            # If the image has changed and there was an old image
            if old_instance.image and old_instance.image.name != instance.image.name:
                if old_instance.image.name != 'game_images/default_game.jpg':
                    # Store the old image name to delete later
                    instance._old_image_name = old_instance.image.name
        except Game.DoesNotExist:
            pass


# Signal to handle when an image is deleted
@receiver(post_delete, sender=Game)
def delete_game_image(sender, instance, **kwargs):
    """
    Delete the image file from S3 when the Game instance is deleted,
    unless it's the default image.
    """
    if instance.image and instance.image.name != 'game_images/default_game.jpg':
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
                Key=f"media/{instance.image.name}"
            )
            print(f"Deleted S3 image: media/{instance.image.name}")
        except Exception as e:
            print(f"Error deleting image from S3: {e}")