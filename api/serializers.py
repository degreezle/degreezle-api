from rest_framework import serializers
from api.models import Solution


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
    solution = serializers.ListField(allow_empty=False, child=serializers.IntegerField(label='Solution'))

    def save(self):
        puzzle = self.validated_data['puzzle']
        solution = self.validated_data['solution']
        solution, created = Solution.objects.get_or_create(puzzle=puzzle, solution=solution)
        if not created:
            solution.count += 1
            solution.save()
        return solution

    class Meta:
        model = Solution
        fields = ['token', 'puzzle', 'solution', 'count']
        read_only_fields = ['token', 'count']
