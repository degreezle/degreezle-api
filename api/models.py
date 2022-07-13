from django.contrib.postgres.fields import ArrayField
from django.utils.crypto import get_random_string   
from django.db import models

class Puzzle(models.Model):
    start_movie_id = models.IntegerField(null=False, blank=False)
    end_movie_id = models.IntegerField(null=False, blank=False)
    object_created = models.DateTimeField(auto_now_add=True)
    object_modified = models.DateTimeField(auto_now=True)

class Solution(models.Model):
    token = models.CharField(max_length=100, unique=True)
    puzzle = models.ForeignKey(
        Puzzle,
        on_delete=models.CASCADE,
        related_name='solutions',
        related_query_name="solution", 
        blank=True,
        null=True,
    )
    solution = ArrayField(models.IntegerField(), unique=True)
    object_created = models.DateTimeField(auto_now_add=True)
    object_modified = models.DateTimeField(auto_now=True)

    @classmethod
    def generate_token(cls):
        return get_random_string(length=32)