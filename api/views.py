from rest_framework.views import APIView
from rest_framework.response import Response

from api.utils import get_movie_cast, get_persons_filmography
from api.serializers import CastMemberSerializer, MovieCreditSerializer


class CrewMemberAPI(APIView):
    """
    View to list all cast members for the movie on tmdb.
    """

    def get(self, _, movie_id):
        """
        Return a list of cast members for the movie on tmdb.
        """
        serializer = CastMemberSerializer(data=get_movie_cast(movie_id), many=True)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.validated_data)


class FilmographyAPI(APIView):
    """
    View to list all movies for the person on tmdb.
    """

    def get(self, _, person_id):
        """
        Return a list of movies for the person on tmdb.
        """
        serializer = MovieCreditSerializer(data=get_persons_filmography(person_id), many=True)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.validated_data)

