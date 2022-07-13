from django.core.management.base import BaseCommand

from api.models import Puzzle, Solution

class Command(BaseCommand):
    help = 'Creates an initial puzzle in the db'

    def handle(self, *args, **options):
        puzzle, _ = Puzzle.objects.get_or_create(start_movie_id=935516, end_movie_id=744)
        Solution.objects.get_or_create(token='xxx', puzzle=puzzle, solution=[935516,62752,466272,138,319,893,744])
        self.stdout.write(self.style.SUCCESS('Created.'))