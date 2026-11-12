"""REST API: /api/v1/workouts/, /api/v1/meals/, /api/v1/weight/, /api/v1/summary/

Authenticate with an API key (Authorization: Bearer fh_...) or a browser session. A user only ever sees their
own records; someone else's record answers 404.
"""
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import mixins, serializers, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from . import analytics
from .models import BodyMetric, Exercise, Meal, Workout, profile_for


def _not_future(value):
    if value > timezone.localdate():
        raise serializers.ValidationError('The date cannot be in the future.')
    return value


class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = ['id', 'name', 'sets', 'reps', 'weight_kg']
        read_only_fields = ['id']


class WorkoutSerializer(serializers.ModelSerializer):
    exercises = ExerciseSerializer(many=True, required=False)
    volume_kg = serializers.DecimalField(max_digits=10, decimal_places=1, read_only=True)

    class Meta:
        model = Workout
        fields = ['id', 'date', 'name', 'duration_min', 'notes', 'exercises', 'volume_kg', 'created_at']
        read_only_fields = ['id', 'volume_kg', 'created_at']

    validate_date = staticmethod(_not_future)

    def validate_exercises(self, value):
        if len(value) > settings.MAX_EXERCISES_PER_WORKOUT:
            raise serializers.ValidationError(f'At most {settings.MAX_EXERCISES_PER_WORKOUT} exercises per workout.')
        return value

    def validate(self, attrs):
        if self.instance is None:
            user = self.context['request'].user
            if Workout.objects.filter(owner=user).count() >= settings.MAX_WORKOUTS_PER_USER:
                raise serializers.ValidationError(f'You have reached the limit of {settings.MAX_WORKOUTS_PER_USER} workouts.')
        return attrs

    @transaction.atomic
    def create(self, validated):
        exercises = validated.pop('exercises', [])
        workout = Workout.objects.create(owner=self.context['request'].user, **validated)
        Exercise.objects.bulk_create([Exercise(workout=workout, **e) for e in exercises])
        return workout

    @transaction.atomic
    def update(self, instance, validated):
        exercises = validated.pop('exercises', None)
        for key, value in validated.items():
            setattr(instance, key, value)
        instance.save()
        if exercises is not None:  # sending a list replaces the exercises; leaving it out keeps them
            instance.exercises.all().delete()
            Exercise.objects.bulk_create([Exercise(workout=instance, **e) for e in exercises])
        return instance


class MealSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meal
        fields = ['id', 'date', 'kind', 'name', 'calories', 'protein_g', 'carbs_g', 'fat_g']
        read_only_fields = ['id']

    validate_date = staticmethod(_not_future)

    def validate(self, attrs):
        day = attrs.get('date') or (self.instance.date if self.instance else None)
        if self.instance is None and day:
            user = self.context['request'].user
            if Meal.objects.filter(owner=user, date=day).count() >= settings.MAX_MEALS_PER_DAY:
                raise serializers.ValidationError(f'At most {settings.MAX_MEALS_PER_DAY} meals per day.')
        return attrs

    def create(self, validated):
        return Meal.objects.create(owner=self.context['request'].user, **validated)


class WeightSerializer(serializers.ModelSerializer):
    class Meta:
        model = BodyMetric
        fields = ['id', 'date', 'weight_kg']
        read_only_fields = ['id']
        extra_kwargs = {'date': {'required': True}}
        validators = []  # one entry per day is handled in create()

    validate_date = staticmethod(_not_future)

    def create(self, validated):
        obj, _ = BodyMetric.objects.update_or_create(
            owner=self.context['request'].user, date=validated['date'], defaults={'weight_kg': validated['weight_kg']})
        return obj

    def update(self, instance, validated):
        if 'date' in validated and validated['date'] != instance.date and \
                BodyMetric.objects.filter(owner=instance.owner, date=validated['date']).exists():
            raise serializers.ValidationError({'date': 'You already have a weight for that day.'})
        return super().update(instance, validated)


class OwnedViewSet(viewsets.ModelViewSet):
    model = None

    def get_queryset(self):
        return self.model.objects.filter(owner=self.request.user)


class WorkoutViewSet(OwnedViewSet):
    model = Workout
    serializer_class = WorkoutSerializer

    def get_queryset(self):
        return super().get_queryset().prefetch_related('exercises')


class MealViewSet(OwnedViewSet):
    model = Meal
    serializer_class = MealSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        day = self.request.query_params.get('date')
        if day:
            try:
                qs = qs.filter(date=serializers.DateField().to_internal_value(day))
            except serializers.ValidationError:
                raise serializers.ValidationError({'date': 'Use the format YYYY-MM-DD.'}) from None
        return qs


class WeightViewSet(OwnedViewSet):
    model = BodyMetric
    serializer_class = WeightSerializer


class SummaryView(APIView):
    def get(self, request):
        profile = profile_for(request.user)
        data = analytics.dashboard(request.user, profile)
        latest = data['latest_weight']
        return Response({
            'workouts_this_week': data['week_done'], 'weekly_workout_target': data['week_target'],
            'minutes_this_week': data['week_minutes'], 'streak_days': data['streak'],
            'calories_today': data['today']['calories'], 'calorie_target': data['calorie_target'],
            'protein_g_today': data['today']['protein'], 'carbs_g_today': data['today']['carbs'],
            'fat_g_today': data['today']['fat'],
            'latest_weight_kg': str(latest.weight_kg) if latest else None,
            'target_weight_kg': str(data['target_weight']) if data['target_weight'] else None,
        })
