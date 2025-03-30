from django.db import models
from django.contrib.auth.models import User
from django.db.models import JSONField
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.db import migrations

class Game(models.Model):
    name = models.CharField(max_length=300)
    description = models.TextField()
    release_date = models.DateField()
    studio = models.CharField(max_length=300) # Developer or studio
    genres = JSONField(default=list, blank=True) # List of genres
    platforms = JSONField(default=list, blank=True) # List of platforms
    likes = models.IntegerField(default=0)
    liked_by = models.ManyToManyField(User, related_name='liked_games', blank=True)
    added_by = models.ForeignKey(User, on_delete=models.CASCADE)

    # Approach 1: Set default parameter in ImageField
    image = models.ImageField(
        upload_to='game_images/',
        null=True,
        blank=True,
        default='game_images/default_game.jpg'  # Path to your default image in MEDIA_ROOT
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

    def __str__(self):
        return self.name

    # Approach 2: Override the save method
    def save(self, *args, **kwargs):
        # If no image is provided, set the default image
        if not self.image:
            self.image = 'game_images/default_game.jpg'
        super().save(*args, **kwargs)

    # Property method to always get an image path
    @property
    def image_url(self):
        if self.image and hasattr(self.image, 'url'):
            return self.image.url
        else:
            return '/media/game_images/default_game.jpg'  # URL to default image


# Signal to handle when an image is deleted
@receiver(post_delete, sender=Game)
def delete_game_image(sender, instance, **kwargs):
    # Don't delete the default image
    if instance.image and instance.image.name != 'game_images/default_game.jpg':
        # Delete the file from storage
        instance.image.delete(False)
