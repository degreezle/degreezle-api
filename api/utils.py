import logging
import toolz
import datetime
import pytz

import tmdbsimple as tmdb
from requests.exceptions import HTTPError
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.gis.geoip2 import GeoIP2

from cache_memoize import cache_memoize as cache
from rest_framework import status
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from api.models import Puzzle, Solution
from api.serializers import CrewMemberSerializer, MovieCreditSerializer, PuzzleSerializer
from degreezle.settings import CACHE_TIMEOUT_IN_SECONDS

logger = logging.getLogger(__name__)


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
    key_generator_callable=lambda *args, **kwargs: 'persons_info' + str(args[0]), 
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


def get_puzzle(request, puzzle_id = None):    
    try:
        puzzle = Puzzle.objects.get(pk=puzzle_id)
    except Puzzle.DoesNotExist:
        try:
            identified_local_datetime = datetime.datetime.now(
                pytz.timezone(get_client_timezone(request))
            )
        except:
            identified_local_datetime = None
        finally:
            puzzle = Puzzle.objects.filter(
                date_active=identified_local_datetime
            ).first()

    if not puzzle:
        puzzle = Puzzle.objects.first()

    serializer = PuzzleSerializer(
        data={
            'id': puzzle.id,
            'start_movie': get_movie_info(puzzle.start_movie_id),
            'end_movie': get_movie_info(puzzle.end_movie_id), 
            'identified_local_datetime': identified_local_datetime, 
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


def get_puzzle_metrics():
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


def order_by_popularity_and_deduplicate(items):
    items = toolz.unique(items, key=lambda x: x['id'])
    return sorted(items, key=lambda x: x['popularity'], reverse=True)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_client_timezone(request):
    try:
        timezone = GeoIP2().country(get_client_ip(request))['time_zone']
    except:
        timezone = 'America/Los_Angeles'
    return timezone