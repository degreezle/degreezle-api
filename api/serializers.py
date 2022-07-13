from django.contrib.auth.models import User, Group
from api.models import Solution
from rest_framework import serializers


class CastMemberSerializer(serializers.Serializer):
    name = serializers.CharField()
    profile_path = serializers.CharField(allow_null=True)
    id = serializers.IntegerField()

class MovieCreditSerializer(serializers.Serializer):
    title = serializers.CharField()
    poster_path = serializers.CharField(allow_null=True)
    id = serializers.IntegerField()

class PuzzleSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    start_movie = MovieCreditSerializer()
    end_movie = MovieCreditSerializer()

class SolutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Solution
        fields = ['token', 'puzzle', 'solution']
        read_only_fields = ['token']
