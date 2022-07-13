from api.serializers import SolutionSerializer
from rest_framework.views import APIView
from rest_framework.response import Response

from api.utils import get_movie_cast, get_persons_filmography, get_persons_info, get_movie_info, get_puzzle, get_solution


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


class InitPuzzleAPI(APIView):
    """
    Init you puzzle by getting the start and end movie info.
    """

    def get(self, _):
        """
        Init you puzzle by getting the start and end movie info.
        """
        return Response(get_puzzle())


class SolutionAPI(APIView):
    """
    Create or view a solution to a puzzle.
    """

    def get(self, _, token):
        """
        Get the solution to a puzzle given a token.
        """
        return Response(get_solution(token))

    def post(self, request, token):
        """
        Init you puzzle by getting the start and end movie info.
        """
        serializer = SolutionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
