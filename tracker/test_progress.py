from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import ExerciseSet
from .testutils import make_user, make_workout


class ProgressPageTests(TestCase):
    def setUp(self):
        self.user = make_user('progress-user')
        self.client.force_login(self.user)

    def test_empty_account_gets_helpful_start_state(self):
        response = self.client.get(reverse('tracker:progress'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Your strength story starts with a workout.')

    def test_progress_uses_completed_sets_and_only_own_data(self):
        workout = make_workout(self.user, ago=3, exercises=(('Squat', 2, 5, '80'),))
        exercise = workout.exercises.get()
        ExerciseSet.objects.filter(exercise=exercise).update(is_completed=True)
        next_workout = make_workout(self.user, ago=1, name='Leg day 2', exercises=(('Squat', 2, 5, '90'),))
        ExerciseSet.objects.filter(exercise__workout=next_workout).update(is_completed=True)

        response = self.client.get(reverse('tracker:progress'), {'exercise': 'Squat'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['personal_record'], Decimal('90.0'))
        self.assertEqual(response.context['session_count'], 2)
        self.assertEqual(response.context['total_sets'], 4)
        self.assertContains(response, 'Squat')
        self.assertContains(response, '90.0 kg')

    def test_uncompleted_sets_do_not_create_strength_records(self):
        make_workout(self.user, exercises=(('Bench press', 3, 8, '60'),))
        response = self.client.get(reverse('tracker:progress'))
        self.assertIsNone(response.context['personal_record'])
        self.assertEqual(response.context['session_count'], 0)

    def test_another_users_exercise_is_never_selectable(self):
        other = make_user('another-user')
        make_workout(other, exercises=(('Secret lift', 3, 8, '100'),))
        response = self.client.get(reverse('tracker:progress'))
        self.assertNotContains(response, 'Secret lift')
        self.assertEqual(response.context['exercise_names'], [])
