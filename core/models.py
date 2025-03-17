from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_delete
from django.dispatch import receiver

class Game(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    release_date = models.DateField()
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


class GameLog(models.Model):
    STATUS_CHOICES = [
        ('played', 'Played'),
        ('abandoned', 'Abandoned'),
        ('shelved', 'Shelved'),
        ('completed', 'Completed'),
        ('wishlist', 'Wishlist'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="logs")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='played')
    notes = models.TextField(blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    hours_played = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'game')

    def __str__(self):
        return f"{self.user.username} - {self.game.title} - {self.status}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    favorite_games = models.ManyToManyField(Game, related_name="favorites", blank=True)
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        null=True,
        blank=True,
        default='profile_pictures/default_profile.jpg'
    )

    def __str__(self):
        return self.user.username

    @property
    def profile_picture_url(self):
        if self.profile_picture and hasattr(self.profile_picture, 'url'):
            return self.profile_picture.url
        else:
            return '/media/profile_pictures/default_profile.jpg'

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, related_name="comments", on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(User, related_name="liked_comments", blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name="replies")

    def __str__(self):
        return f'Comment by {self.user.username} on {self.game.name}'
