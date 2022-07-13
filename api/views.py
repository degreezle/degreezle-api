from rest_framework.views import APIView
from rest_framework.response import Response

from api.utils import get_movie_cast, get_persons_filmography, get_persons_info, get_movie_info


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
        return Response(get_movie_cast(movie_id))


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
