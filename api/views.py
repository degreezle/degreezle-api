import tmdbsimple as tmdb

from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import CastMemberSerializer


class CrewMemberAPI(APIView):
    """
    View to list all cast members for the movie on tmdb.
    """

    def get(self, request, movie_id):
        """
        Return a list of cast members for the movie on tmdb.
        """
        tmdb.API_KEY = settings.TMDB_API_KEY
        movie = tmdb.Movies(movie_id)
        serializer = CastMemberSerializer(data=movie.credits()['cast'], many=True)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.validated_data)


def index(request):
    return HttpResponse("Hello, world. You're at the api index.")