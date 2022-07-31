from django.contrib.postgres.fields import ArrayField
from django.utils.crypto import get_random_string  
from django.db import models

import numpy as np


def generate_token():
    return get_random_string(length=8)


class Puzzle(models.Model):
    start_movie_id = models.IntegerField(null=False, blank=False)
    end_movie_id = models.IntegerField(null=False, blank=False)
    date_active = models.DateField(null=True, blank=True)
    object_created = models.DateTimeField(auto_now_add=True)
    object_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        string = f'Puzzle #{self.id}'
        if self.date_active:
            string += self.date_active.strftime(": %Y%m%d")
        return string

    @property
    def num_solved(self):
        return sum(self.solutions.values_list('count', flat=True))

    @property
    def num_solutions(self):
        return self.solutions.count()

    @property
    def shortest_solution(self):
        lengths = self.all_solution_lengths()
        if lengths:
            return min(lengths)

    @property
    def longest_solution(self):
        lengths = self.all_solution_lengths()
        if lengths:
            return max(lengths)

    @property
    def average_steps(self):
        lengths = self.all_solution_lengths()
        if lengths:
            return np.mean(lengths)

    @property
    def median_steps(self):
        lengths = self.all_solution_lengths()
        if lengths:
            return np.median(lengths)

    def all_solution_lengths(self):
        solution_lengths = []
        for solution in self.solutions.all():
            solution_lengths += [solution.num_degrees] * solution.count
        return solution_lengths

class Solution(models.Model):
    token = models.CharField(max_length=100, default=generate_token, unique=True)
    puzzle = models.ForeignKey(
        Puzzle,
        on_delete=models.CASCADE,
        related_name='solutions',
        related_query_name='solution',
        blank=False,
        null=False,
    )
    solution = ArrayField(models.IntegerField(), unique=True)
    count = models.IntegerField(default=0)
    object_created = models.DateTimeField(auto_now_add=True)
    object_modified = models.DateTimeField(auto_now=True)

    @property
    def num_degrees(self):
        if self.solution:
            return len(self.solution) - 1
