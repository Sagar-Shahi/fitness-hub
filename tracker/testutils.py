"""Helpers shared by the test modules."""
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import BodyMetric, Exercise, Meal, Workout

PASSWORD = 'S3cure-pass-91-xyz'


def make_user(name='sam'):
    return get_user_model().objects.create_user(name, f'{name}@example.com', PASSWORD)


def days_ago(n):
    return timezone.localdate() - timedelta(days=n)


def make_workout(owner, ago=0, name='Push day', minutes=45, exercises=((('Bench press', 4, 8, '60')),)):
    workout = Workout.objects.create(owner=owner, date=days_ago(ago), name=name, duration_min=minutes)
    for n, sets, reps, kg in exercises:
        Exercise.objects.create(workout=workout, name=n, sets=sets, reps=reps, weight_kg=Decimal(kg))
    return workout


def make_meal(owner, ago=0, calories=500, protein=30, carbs=50, fat=15, name='Lunch', kind='lunch'):
    return Meal.objects.create(owner=owner, date=days_ago(ago), kind=kind, name=name, calories=calories,
                               protein_g=protein, carbs_g=carbs, fat_g=fat)


def make_weight(owner, ago=0, kg='80.0'):
    return BodyMetric.objects.create(owner=owner, date=days_ago(ago), weight_kg=Decimal(kg))
