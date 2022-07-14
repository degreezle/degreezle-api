import logging

import tmdbsimple as tmdb
from requests.exceptions import HTTPError
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from cache_memoize import cache_memoize as cache
from rest_framework import status
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from api.serializers import CastMemberSerializer, MovieCreditSerializer, PuzzleSerializer
from degreezle.settings import CACHE_TIMEOUT_IN_SECONDS

logger = logging.getLogger(__name__)


@cache(CACHE_TIMEOUT_IN_SECONDS)
def get_movie_cast(movie_id):
    """
    Returns a list of cast members from tmdb
    ordered by popularity
    or raises HTTPError
    """
    tmdb.API_KEY = settings.TMDB_API_KEY
    movie = tmdb.Movies(movie_id)
    credits = movie.credits().get('cast', [])

    serializer = CastMemberSerializer(
        data=order_by_popularity(credits), many=True)
    serializer.is_valid(raise_exception=True)

    return serializer.validated_data


@cache(CACHE_TIMEOUT_IN_SECONDS)
def get_persons_filmography(person_id):
    """
    Returns a list of movies from tmdb
    ordered by popularity
    or raises HTTPError
    """
    tmdb.API_KEY = settings.TMDB_API_KEY
    person = tmdb.People(person_id)
    credits = person.movie_credits().get('cast', [])

    serializer = MovieCreditSerializer(
        data=order_by_popularity(credits), many=True)
    serializer.is_valid(raise_exception=True)

    return serializer.validated_data


@cache(CACHE_TIMEOUT_IN_SECONDS)
def get_movie_info(movie_id):
    """
    Returns info about a movie from tmdb
    ordered by popularity
    or raises HTTPError
    """
    tmdb.API_KEY = settings.TMDB_API_KEY
    movie = tmdb.Movies(movie_id)

    serializer = MovieCreditSerializer(
        data=movie.info())
    serializer.is_valid(raise_exception=True)

    return serializer.validated_data


@cache(CACHE_TIMEOUT_IN_SECONDS)
def get_persons_info(person_id):
    """
    Returns info about a person from tmdb
    or raises HTTPError
    """
    tmdb.API_KEY = settings.TMDB_API_KEY
    person = tmdb.People(person_id)

    serializer = CastMemberSerializer(
        data=person.info())
    serializer.is_valid(raise_exception=True)

    return serializer.validated_data


def get_puzzle():
    from api.models import Puzzle
    puzzle = Puzzle.objects.first()

    serializer = PuzzleSerializer(
        data={
            'id': puzzle.id,
            'start_movie': get_movie_info(puzzle.start_movie_id),
            'end_movie': get_movie_info(puzzle.end_movie_id)
        })
    serializer.is_valid(raise_exception=True)

    return serializer.validated_data


def get_solution(token):
    from api.models import Solution
    solution = Solution.objects.get(token=token)
    return {
        'token': solution.token,
        'puzzle': solution.puzzle.id,
        'solution': [
            get_movie_info(id) if index % 2 == 0 else get_persons_info(id)
            for index, id in enumerate(solution.solution)
        ]
    }


def get_puzzle_metrics():
    from api.models import Puzzle
    puzzle = Puzzle.objects.first()
    return {
        'num_solved': puzzle.num_solved, 
        'shortest_solution': puzzle.shortest_solution, 
        'average_steps': puzzle.average_steps,
        'median_steps': puzzle.median_steps,
    }

def api_exception_handler(exc, context):
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    if isinstance(exc, ValidationError):
        logger.warning('TMDB response returned unexpected format')
        # return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if isinstance(exc, ObjectDoesNotExist):
        logger.warning(f'DB ID Not Found')
        return Response(status=status.HTTP_404_NOT_FOUND)

    if isinstance(exc, HTTPError):
        if exc.response.status_code == 404:
            logger.warning(f'Object ID Not Found {exc.request.url}')
            return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            logger.warning('TMDB failed. Possible invalid key')
            return Response(status=status.HTTP_502_BAD_GATEWAY)

    # returns response as handled normally by the framework
    return response


def order_by_popularity(items):
    return sorted(items, key=lambda x: x['popularity'], reverse=True)

