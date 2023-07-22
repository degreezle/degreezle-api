from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe

from urllib.parse import urlencode

from api.models import Puzzle, Solution


@admin.register(Puzzle)
class PuzzleAdmin(admin.ModelAdmin):
    readonly_fields = (
        'id',
        'link_to_first_film',
        'link_to_last_film',
        'num_solutions',
        'num_solved',
        'shortest_solution',
        'longest_solution',
        'average_steps',
        'median_steps',
        'link_to_solution_list',
    )
    list_display = readonly_fields + ('date_active', )
    fieldsets = (
        ('Films', {
            'fields': (
                ('start_movie_id', 'end_movie_id'), 
                ('link_to_first_film', 'link_to_last_film'),
            )
        }),
        ('Metadata', {
            'fields': (('date_active', 'author'), )
        }),
        ('Metrics', {
            'fields': (
                ('num_solved', 'num_solutions', 'link_to_solution_list'),
                ('shortest_solution', 'longest_solution', 'average_steps', 'median_steps'),
            )
        })
    )
    ordering = ('-date_active', )

    def link_to_first_film(self, obj):
        if obj.start_movie_id:
            url = f'https://themoviedb.org/movie/{obj.start_movie_id}'
            return mark_safe(f'<a href={url} target="_blank">{obj.start_movie_id}</a>')
        return '-'

    def link_to_last_film(self, obj):
        if obj.end_movie_id:
            url = f'https://themoviedb.org/movie/{obj.end_movie_id}'
            return mark_safe(f'<a href={url} target="_blank">{obj.end_movie_id}</a>')
        return '-'

    def link_to_solution_list(self, obj):
        if obj.solutions.exists():
            base_url = reverse('admin:api_solution_changelist')
            query_string = urlencode({'puzzle': obj.id})
            url = f'{base_url}?{query_string}'
            return mark_safe(f'<a href={url}>View solutions</a>')
        elif all([getattr(obj, i) for i in ('id', 'start_movie_id', 'end_movie_id')]):
            base_url = reverse('admin:api_solution_add')
            query_string = urlencode({
                'puzzle': obj.id,
                'solution': f'{obj.start_movie_id},{obj.end_movie_id}',
            })
            url = f'{base_url}?{query_string}'
            return mark_safe(f'<a href={url}>Add a solution</a>')
        return '-'


@admin.register(Solution)
class SolutionAdmin(admin.ModelAdmin):
    readonly_fields = (
        'id',
        'puzzle_link',
        'count',
        'solution_view_link',
        'num_degrees',
        'object_created',
    )
    list_display = readonly_fields
    fieldsets = (
        ('Puzzle', {
            'fields': ('puzzle', 'puzzle_link')
        }),
        ('Solution', {
            'fields': (('count', 'num_degrees', 'solution'), ),
        }),
        ('Access', {
            'fields': (('token', 'solution_view_link'), )
        }),
    )

    list_filter = ('puzzle', )

    def puzzle_link(self, obj):
        if obj.puzzle:
            url = reverse('admin:api_puzzle_change', args=(obj.puzzle.id, ))
            return mark_safe(f'<a href={url}>{obj.puzzle}</a>')
        return '-'

    def solution_view_link(self, obj):
        if obj.id:
            url = f'https://filminthega.ps/solution/{obj.token}'
            return mark_safe(f'<a href={url} target="_blank">View solution</a>')
        return '-'
