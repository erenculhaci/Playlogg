from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.crypto import get_random_string
from games.models import Game


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    favorite_games = models.ManyToManyField('games.Game', related_name="favorites", blank=True)
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        null=True,
        blank=True,
        default='profile_pictures/default_profile.jpg'
    )
    is_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.user.username

    @property
    def profile_picture_url(self):
        if self.profile_picture and hasattr(self.profile_picture, 'url'):
            return self.profile_picture.url
        else:
            return '/media/profile_pictures/default_profile.jpg'

    def generate_verification_token(self):
        self.verification_token = get_random_string(64)
        self.save()
        return self.verification_token


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