import logging

import tmdbsimple as tmdb
from requests.exceptions import HTTPError
from django.conf import settings

from cache_memoize import cache_memoize as cache
from rest_framework import status
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from degreezle.settings import CACHE_TIMEOUT_IN_SECONDS

logger = logging.getLogger(__name__)

@cache(CACHE_TIMEOUT_IN_SECONDS)
def get_movie_cast(movie_id):
    """
    Returns a list of cast members from tmdb
    or raises HTTPError
    """
    tmdb.API_KEY = settings.TMDB_API_KEY
    movie = tmdb.Movies(movie_id)
    print('yoooooooo')
    return movie.credits().get('cast', [])


@cache(CACHE_TIMEOUT_IN_SECONDS)
def get_persons_filmography(person_id):
    """
    Returns a list of movies from tmdb
    or raises HTTPError
    """
    tmdb.API_KEY = settings.TMDB_API_KEY
    person = tmdb.People(person_id)
    return person.movie_credits().get('cast', [])


def api_exception_handler(exc, context):
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    if isinstance(exc, ValidationError):
        logger.warning('TMDB response returned unexpected format')
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if isinstance(exc, HTTPError):
        if exc.response.status_code == 404:
            logger.warning(f'Object ID Not Found {exc.request.url}')
            return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            logger.warning('TMDB failed. Possible invalid key')
            return Response(status=status.HTTP_502_BAD_GATEWAY)

    # returns response as handled normally by the framework
    return response