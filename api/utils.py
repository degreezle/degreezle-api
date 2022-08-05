import logging
import toolz
import datetime
import pytz

import tmdbsimple as tmdb
from requests.exceptions import HTTPError
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.gis.geoip2 import GeoIP2
from django.db import models

from cache_memoize import cache_memoize as cache
from rest_framework import status
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from api.models import Puzzle, Solution
from api.serializers import CrewMemberSerializer, MovieCreditSerializer, PuzzleSerializer
from degreezle.settings import CACHE_TIMEOUT_IN_SECONDS

logger = logging.getLogger(__name__)


class ArrayLength(models.Func):
    function = 'CARDINALITY'


@cache(CACHE_TIMEOUT_IN_SECONDS)
def get_movie_cast_and_crew(movie_id):
    """
    Returns a list of cast members from tmdb
    ordered by popularity
    or raises HTTPError
    """
    tmdb.API_KEY = settings.TMDB_API_KEY
    movie = tmdb.Movies(movie_id)
    credits = movie.credits()
    cast = credits.get('cast', [])
    crew = credits.get('crew', [])
    credits = order_by_popularity_and_deduplicate(cast + crew)

    serializer = CrewMemberSerializer(data=credits, many=True)
    serializer.is_valid(raise_exception=True)

    for person_data in serializer.validated_data:
        get_persons_info(person_data['id'], force_cache=person_data)

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
    credits = person.movie_credits()
    cast = credits.get('cast', [])
    crew = credits.get('crew', [])
    credits = order_by_popularity_and_deduplicate(cast + crew)

    serializer = MovieCreditSerializer(data=credits, many=True)
    serializer.is_valid(raise_exception=True)

    for movie_data in serializer.validated_data:
        get_movie_info(movie_data['id'], force_cache=movie_data)

    return serializer.validated_data


@cache(
    CACHE_TIMEOUT_IN_SECONDS,
    # Allows force_cache to work
    key_generator_callable=lambda *args, **kwargs: 'movie_info' + str(args[0])
)
def get_movie_info(movie_id, force_cache=None):
    """
    Returns info about a movie from tmdb
    ordered by popularity
    or raises HTTPError
    """
    if force_cache:
        return force_cache

    tmdb.API_KEY = settings.TMDB_API_KEY
    movie = tmdb.Movies(movie_id)

    serializer = MovieCreditSerializer(
        data=movie.info())
    serializer.is_valid(raise_exception=True)

    return serializer.validated_data


@cache(
    CACHE_TIMEOUT_IN_SECONDS,
    # Allows force_cache to work
    key_generator_callable=lambda *args, **kwargs: 'persons_info' + \
    str(args[0]),
)
def get_persons_info(person_id, force_cache=None):
    """
    Returns info about a person from tmdb
    or raises HTTPError
    """
    if force_cache:
        return force_cache

    tmdb.API_KEY = settings.TMDB_API_KEY
    person = tmdb.People(person_id)

    serializer = CrewMemberSerializer(
        data=person.info())
    serializer.is_valid(raise_exception=True)

    return serializer.validated_data


def find_puzzle_and_datetime(request, puzzle_id=None):
    try:
        local_datetime = datetime.datetime.now(
            pytz.timezone(get_client_timezone(request))
        )
    except:
        local_datetime = datetime.datetime.now()
    finally:
        puzzles_available = Puzzle.objects.filter(
            date_active__lte=local_datetime.date() 
        )
    
    if puzzle_id:
        puzzle = puzzles_available.get(pk=puzzle_id)
    else:
        puzzle = puzzles_available.filter(
            date_active=local_datetime.date()
        ).first()

    return puzzle, local_datetime


def get_puzzle(request, puzzle_id=None):
    puzzle, local_datetime = find_puzzle_and_datetime(request, puzzle_id)

    serializer = PuzzleSerializer(
        data={
            'id': puzzle.id,
            'start_movie': get_movie_info(puzzle.start_movie_id),
            'end_movie': get_movie_info(puzzle.end_movie_id),
            'local_datetime': local_datetime.strftime('%Y-%m-%d %H:%M:%S') if local_datetime else None,
            'local_timezone': get_client_timezone(request),
        })
    serializer.is_valid(raise_exception=True)

    return serializer.validated_data


def get_solution(token):
    solution = Solution.objects.get(token=token)
    return {
        'token': solution.token,
        'puzzle': solution.puzzle.id,
        'length': solution.num_degrees,
        'solution': [
            get_movie_info(id) if index % 2 == 0 else get_persons_info(id)
            for index, id in enumerate(solution.solution)
        ]
    }


def get_puzzle_metrics(request, puzzle_id=None):
    puzzle, _ = find_puzzle_and_datetime(request, puzzle_id)
    return {
        'id': puzzle.id,
        'num_solved': puzzle.num_solved,
        'shortest_solution': puzzle.shortest_solution,
        'longest_solution': puzzle.longest_solution,
        'average_steps': puzzle.average_steps,
        'median_steps': puzzle.median_steps,
    }


def get_solution_metrics(token):
    solution = Solution.objects.get(token=token)
    puzzle = solution.puzzle

    solutions_ordered_by_length = solution.puzzle.solutions.annotate(
        solution_length=ArrayLength('solution')
    ).order_by('solution_length')

    return {
        'token': solution.token,
        'shortest_solution_steps': solutions_ordered_by_length.first().num_degrees,
        'longest_solution_steps': solutions_ordered_by_length.last().num_degrees,
        'shortest_solution_token': solutions_ordered_by_length.first().token,
        'longest_solution_token': solutions_ordered_by_length.last().token,
        'count': solution.count - 1,
        'num_steps':  solution.num_degrees,
        'num_solved': puzzle.num_solved,
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


def order_by_popularity_and_deduplicate(items):
    items = toolz.unique(items, key=lambda x: x['id'])
    return sorted(items, key=lambda x: x.get('popularity', 0), reverse=True)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_client_timezone(request):
    try:
        timezone = GeoIP2().city(get_client_ip(request))['time_zone']
    except:
        timezone = 'America/Los_Angeles'
    return timezone
