from games.models import Game
from logs.models import GameLog

def get_liked_games(user):
    return Game.objects.filter(liked_by=user)

def get_games_by_status(user, status=None):
    if status:
        return GameLog.objects.filter(user=user, status=status)
    return GameLog.objects.filter(user=user)