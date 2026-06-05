from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from exercises.models import Exercise, ExerciseCompletion
from .models import UserWorkoutStats


class ProgressViewTests(TestCase):
    def test_progress_requires_login(self):
        resp = self.client.get(reverse('progress'))
        self.assertEqual(resp.status_code, 302)

    def test_progress_logged_in(self):
        u = User.objects.create_user('puser', 'p@example.com', 'pass')
        self.client.login(username='puser', password='pass')
        resp = self.client.get(reverse('progress'))
        self.assertEqual(resp.status_code, 200)

    def test_progress_aggregates_completions(self):
        user = User.objects.create_user('agg', 'agg@test.com', 'pw')
        ex = Exercise.objects.create(
            name='Push-Up',
            category='chest',
            difficulty='beginner',
            equipment='Bodyweight',
            default_reps=15, default_sets=3,
        )
        ExerciseCompletion.objects.create(user=user, exercise=ex, reps=15)
        ExerciseCompletion.objects.create(user=user, exercise=ex, reps=12)

        self.client.login(username='agg', password='pw')
        resp = self.client.get(reverse('progress'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context['completions']), 2)

    def test_progress_shows_stats_when_completions_exist(self):
        user = User.objects.create_user('st', 'st@test.com', 'pw')
        ex = Exercise.objects.create(
            name='Plank',
            category='core',
            difficulty='beginner',
            equipment='Bodyweight',
            default_reps=1, default_sets=3,
        )
        ExerciseCompletion.objects.create(user=user, exercise=ex, reps=1)
        UserWorkoutStats.objects.create(
            user=user, total_workouts=1, current_streak=1, longest_streak=1,
        )
        self.client.login(username='st', password='pw')
        resp = self.client.get(reverse('progress'))
        self.assertIsNotNone(resp.context['stats'])
        self.assertEqual(resp.context['stats'].total_workouts, 1)


class LogExerciseViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('logger', 'l@test.com', 'pw')
        self.ex = Exercise.objects.create(
            name='Squat',
            category='legs',
            difficulty='beginner',
            equipment='Bodyweight',
            default_reps=20, default_sets=3,
        )

    def test_log_exercise_creates_completion(self):
        self.client.login(username='logger', password='pw')
        resp = self.client.post(
            reverse('log-exercise', args=[self.ex.slug]),
            data={'reps': '20', 'notes': 'felt strong'},
        )
        self.assertEqual(resp.status_code, 302)
        c = ExerciseCompletion.objects.get(user=self.user, exercise=self.ex)
        self.assertEqual(c.reps, 20)
        self.assertEqual(c.notes, 'felt strong')


class ProgressEditDeleteTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('ed', 'ed@test.com', 'pw')
        self.other = User.objects.create_user('other', 'o@test.com', 'pw')
        self.ex = Exercise.objects.create(
            name='Lunge',
            category='legs',
            difficulty='beginner',
            equipment='Bodyweight',
            default_reps=12, default_sets=3,
        )
        self.completion = ExerciseCompletion.objects.create(
            user=self.user, exercise=self.ex, reps=10,
        )

    def test_edit_completion(self):
        self.client.login(username='ed', password='pw')
        resp = self.client.post(
            reverse('progress-edit', args=[self.completion.pk]),
            data={'reps': '15', 'notes': 'updated'},
        )
        self.assertEqual(resp.status_code, 302)
        self.completion.refresh_from_db()
        self.assertEqual(self.completion.reps, 15)

    def test_cannot_edit_others_completion(self):
        self.client.login(username='other', password='pw')
        resp = self.client.get(
            reverse('progress-edit', args=[self.completion.pk]),
        )
        self.assertEqual(resp.status_code, 404)

    def test_delete_completion(self):
        self.client.login(username='ed', password='pw')
        resp = self.client.post(
            reverse('progress-delete', args=[self.completion.pk]),
        )
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(
            ExerciseCompletion.objects.filter(pk=self.completion.pk).exists()
        )

    def test_cannot_delete_others_completion(self):
        self.client.login(username='other', password='pw')
        resp = self.client.post(
            reverse('progress-delete', args=[self.completion.pk]),
        )
        self.assertEqual(resp.status_code, 404)
        self.assertTrue(
            ExerciseCompletion.objects.filter(pk=self.completion.pk).exists()
        )
