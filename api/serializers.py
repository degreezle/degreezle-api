from django.contrib.auth.models import User, Group
from rest_framework import serializers


class CastMemberSerializer(serializers.Serializer):
    name = serializers.CharField()
    profile_path = serializers.CharField(allow_null=True)
    id = serializers.IntegerField()

class MovieCreditSerializer(serializers.Serializer):
    title = serializers.CharField()
    poster_path = serializers.CharField(allow_null=True)
    id = serializers.IntegerField()