from django.db import models
from api.serializers import SolutionSerializer
from rest_framework.response import Response
from rest_framework.views import APIView

from api.utils import (
    get_movie_cast_and_crew,
    get_persons_filmography,
    get_persons_info,
    get_movie_info,
    get_puzzle,
    get_puzzle_metrics,
    get_solution,
)

class ArrayLength(models.Func):
    function = 'CARDINALITY'


class MovieCrewAPI(APIView):
    """
    View to list all cast members for the movie on tmdb
    ordered by popularity.
    """

    def get(self, _, movie_id):
        """
        Return a list of cast members for the movie on tmdb
        ordered by popularity.
        """
        return Response(get_movie_cast_and_crew(movie_id))


class FilmographyAPI(APIView):
    """
    View to list all movies for the person on tmdb
    ordered by popularity.
    """

    def get(self, _, person_id):
        """
        Return a list of movies for the person on tmdb
        ordered by popularity.
        """
        return Response(get_persons_filmography(person_id))


class PersonInfoAPI(APIView):
    """
    View info about a specific person on tmdb.
    """

    def get(self, _, person_id):
        """
        View info about a specific person on tmdb.
        """
        return Response(get_persons_info(person_id))


class MovieInfoAPI(APIView):
    """
    View info about a specific movie on tmdb.
    """

    def get(self, _, movie_id):
        """
        View info about a specific movie on tmdb.
        """
        return Response(get_movie_info(movie_id))


class PuzzleAPI(APIView):
    """
    Initialize a puzzle by getting first and last movies.
    """

    def get(self, request, puzzle_id = None):
        return Response(get_puzzle(request, puzzle_id))


class SolutionAPI(APIView):
    """
    Create or view a solution to a puzzle.
    """

    def get(self, _, token):
        """
        Get the solution to a puzzle given a token.
        """
        return Response(get_solution(token))

    def post(self, request):
        """
        Create or update a Solution with a given path
        """
        serializer = SolutionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        solution = serializer.save()

        solutions_ordered_by_length = solution.puzzle.solutions.annotate(
            solution_length=ArrayLength('solution')
        ).order_by('solution_length')

        return Response({
            'puzzle': solution.puzzle.id,
            'solution': solution.solution,
            'token': solution.token,
            'count': solution.count - 1,
            'shortest_solution': solutions_ordered_by_length.first().token,
            'longest_solution': solutions_ordered_by_length.last().token, 
        })


class MetricsAPI(APIView):
    """
    View metrics about the current puzzle.
    """

    def get(self, request):
        """
        Get the solution to a puzzle given a token.
        """
        return Response(get_puzzle_metrics(request))
