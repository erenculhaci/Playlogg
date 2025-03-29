from django.core.management.base import BaseCommand
from games.igdb_fetch import fetch_all_games_from_igdb

class Command(BaseCommand):
    help = "Fetch all available games from IGDB and store them in the database"

    def handle(self, *args, **kwargs):
        total_games = fetch_all_games_from_igdb()
        self.stdout.write(self.style.SUCCESS(f"Successfully added {total_games} games from IGDB!"))
