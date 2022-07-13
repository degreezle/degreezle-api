from django.contrib import admin

from api.models import Puzzle, Solution

class PuzzleAdmin(admin.ModelAdmin):
    pass

admin.site.register(Puzzle, PuzzleAdmin)

class SolutionAdmin(admin.ModelAdmin):
    pass

admin.site.register(Solution, SolutionAdmin)
