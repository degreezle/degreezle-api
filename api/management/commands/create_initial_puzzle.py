from django.core.management.base import BaseCommand

from api.models import Puzzle

class Command(BaseCommand):
    help = 'Creates an initial puzzle in the db'

    def handle(self, *args, **options):
        Puzzle.objects.get_or_create(start_movie_id=935516, end_movie_id=744)
        self.stdout.write(self.style.SUCCESS('Created.'))