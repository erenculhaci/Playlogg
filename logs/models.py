from django.db import models
from django.contrib.auth.models import User
from games.models import Game

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