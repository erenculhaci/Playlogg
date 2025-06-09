from django.core.management.base import BaseCommand
from games.igdb_fetch import fetch_games_by_popularity


class Command(BaseCommand):
    help = "Fetch games from IGDB sorted by popularity and store them in the database"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Starting to fetch games by popularity from IGDB..."))

        try:
            total_games = fetch_games_by_popularity()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully added {total_games} popular games from IGDB!"
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f"Error occurred while fetching games: {str(e)}"
                )
            )
            raise e