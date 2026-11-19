from decimal import Decimal

from django.urls import reverse
from rest_framework.test import APIClient
from django.test import TestCase

from accounts.models import ApiKey
from .models import Exercise, ExerciseSet, Workout
from .testutils import days_ago, make_user, make_workout


class EmptySetVolumeTests(TestCase):
    def setUp(self):
        self.user = make_user('set-volume')
        self.workout = make_workout(self.user, exercises=())
        self.exercise = Exercise.objects.create(
            workout=self.workout, name='Bench press', sets=2, reps=10, weight_kg=Decimal('40.0')
        )

    def test_deleting_every_set_leaves_zero_completed_volume(self):
        first = ExerciseSet.objects.create(
            exercise=self.exercise, set_number=1, reps=10, weight_kg=Decimal('40.0'), is_completed=True
        )
        second = ExerciseSet.objects.create(
            exercise=self.exercise, set_number=2, reps=8, weight_kg=Decimal('50.0'), is_completed=True
        )
        self.assertEqual(self.workout.volume_kg, Decimal('800.0'))
        self.client.force_login(self.user)
        self.client.post(reverse('tracker:exercise-set-delete', args=[self.workout.pk, self.exercise.pk, first.pk]))
        self.client.post(reverse('tracker:exercise-set-delete', args=[self.workout.pk, self.exercise.pk, second.pk]))
        self.assertEqual(self.workout.volume_kg, Decimal('0'))

    def test_explicit_empty_api_set_list_means_zero_volume(self):
        key, raw = ApiKey.issue(self.user, 'set-volume')
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {raw}')
        response = client.post('/api/v1/workouts/', {
            'date': days_ago(0).isoformat(),
            'name': 'Empty set list',
            'duration_min': 30,
            'exercises': [{
                'name': 'Bench press',
                'sets': 2,
                'reps': 10,
                'weight_kg': '40.0',
                'set_details': [],
            }],
        }, format='json')
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(Decimal(response.json()['volume_kg']), Decimal('0'))
        self.assertEqual(ExerciseSet.objects.filter(exercise__workout__owner=self.user).count(), 0)
