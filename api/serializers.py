from rest_framework import serializers

from api.models import Solution


class CrewMemberSerializer(serializers.Serializer):
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
    local_datetime = serializers.CharField(allow_null=True)
    local_timezone = serializers.CharField()

class SolutionSerializer(serializers.ModelSerializer):
    solution = serializers.ListField(
        allow_empty=False,
        child=serializers.IntegerField(label='Solution'),
    )

    def is_valid(self, raise_exceptions=False):
        from api.utils import get_movie_cast_and_crew, get_persons_filmography

        solution = self.validated_data['solution']
        for i, step in enumerate(solution):
            if i + 1 == len(solution):
                return True

            if i % 2 == 0:
                ids = [c['id'] for c in get_movie_cast_and_crew(step)]
            else:
                ids = [f['id'] for f in get_persons_filmography(step)]

            if solution[i + 1] not in ids:
                return False

    def save(self):
        puzzle = self.validated_data['puzzle']
        solution = self.validated_data['solution']
        solution, _ = Solution.objects.get_or_create(
            puzzle=puzzle,
            solution=solution,
        )
        solution.count += 1
        solution.save()
        return solution

    class Meta:
        model = Solution
        fields = ['token', 'puzzle', 'solution', 'count', 'num_degrees']
        read_only_fields = ['token', 'count', 'num_degrees']
