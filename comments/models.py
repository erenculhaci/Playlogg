from django.db import models
from django.contrib.auth.models import User
from games.models import Game

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
