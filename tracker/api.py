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
from .models import BodyMetric, Exercise, ExerciseSet, Meal, Workout, profile_for
from .nutrition import refresh_profile_calorie_target


def _not_future(value):
    if value > timezone.localdate():
        raise serializers.ValidationError('The date cannot be in the future.')
    return value


class ExerciseSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseSet
        fields = ['id', 'set_number', 'reps', 'weight_kg', 'is_completed', 'is_warmup']
        read_only_fields = ['id']


class ExerciseSerializer(serializers.ModelSerializer):
    set_details = ExerciseSetSerializer(source='set_entries', many=True, required=False)

    class Meta:
        model = Exercise
        fields = ['id', 'name', 'sets', 'reps', 'weight_kg', 'set_details']
        read_only_fields = ['id']

    def validate_set_details(self, value):
        if len(value) > 50:
            raise serializers.ValidationError('At most 50 sets per exercise.')
        numbers = [entry['set_number'] for entry in value]
        if len(numbers) != len(set(numbers)):
            raise serializers.ValidationError('Set numbers must be unique within an exercise.')
        return value

    def create(self, validated):
        # Older API clients send only summary fields. Materialize those as completed
        # sets to preserve their historical volume semantics. An explicit [] means
        # the client intentionally supplied no sets and must remain zero volume.
        set_details = validated.pop('set_entries', None)
        exercise = Exercise.objects.create(**validated)
        if set_details is None:
            set_details = [
                {
                    'set_number': number,
                    'reps': exercise.reps,
                    'weight_kg': exercise.weight_kg,
                    'is_completed': True,
                    'is_warmup': False,
                }
                for number in range(1, exercise.sets + 1)
            ]
        ExerciseSet.objects.bulk_create([
            ExerciseSet(exercise=exercise, **entry) for entry in set_details
        ])
        return exercise

    def update(self, instance, validated):
        set_details = validated.pop('set_entries', None)
        for key, value in validated.items():
            setattr(instance, key, value)
        instance.save()
        if set_details is not None:
            instance.set_entries.all().delete()
            ExerciseSet.objects.bulk_create([
                ExerciseSet(exercise=instance, **entry) for entry in set_details
            ])
        return instance


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
        for exercise_data in exercises:
            ExerciseSerializer().create({'workout': workout, **exercise_data})
        return workout

    @transaction.atomic
    def update(self, instance, validated):
        exercises = validated.pop('exercises', None)
        for key, value in validated.items():
            setattr(instance, key, value)
        instance.save()
        if exercises is not None:  # sending a list replaces the exercises; leaving it out keeps them
            instance.exercises.all().delete()
            for exercise_data in exercises:
                ExerciseSerializer().create({'workout': instance, **exercise_data})
        return instance


class MealSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meal
        fields = ['id', 'date', 'kind', 'name', 'calories', 'protein_g', 'carbs_g', 'fat_g']
        read_only_fields = ['id']

    validate_date = staticmethod(_not_future)

    def validate(self, attrs):
        day = attrs.get('date') or (self.instance.date if self.instance else None)
        if day:
            user = self.context['request'].user
            meals = Meal.objects.filter(owner=user, date=day)
            if self.instance is not None:
                meals = meals.exclude(pk=self.instance.pk)
            if meals.count() >= settings.MAX_MEALS_PER_DAY:
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
        user = self.context['request'].user
        obj, _ = BodyMetric.objects.update_or_create(
            owner=user, date=validated['date'], defaults={'weight_kg': validated['weight_kg']})
        refresh_profile_calorie_target(profile_for(user))
        return obj

    def update(self, instance, validated):
        if 'date' in validated and validated['date'] != instance.date and \
                BodyMetric.objects.filter(owner=instance.owner, date=validated['date']).exists():
            raise serializers.ValidationError({'date': 'You already have a weight for that day.'})
        updated = super().update(instance, validated)
        refresh_profile_calorie_target(profile_for(updated.owner))
        return updated


class OwnedViewSet(viewsets.ModelViewSet):
    model = None

    def get_queryset(self):
        return self.model.objects.filter(owner=self.request.user)


class WorkoutViewSet(OwnedViewSet):
    model = Workout
    serializer_class = WorkoutSerializer

    def get_queryset(self):
        return super().get_queryset().prefetch_related('exercises__set_entries')


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

    def perform_destroy(self, instance):
        owner = instance.owner
        instance.delete()
        refresh_profile_calorie_target(profile_for(owner))


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
