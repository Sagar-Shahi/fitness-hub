from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from goals.models import Goal
from .models import Exercise, ExerciseCompletion


class ExerciseLibraryTests(TestCase):
    def setUp(self):
        self.pull_up = Exercise.objects.create(
            name='Pull-Up',
            category='back',
            difficulty='intermediate',
            equipment='Pull-Up Bar',
            goal='strength',
            default_reps=6, default_sets=3, duration_min=6, calories_per_set=12,
        )
        self.burpee = Exercise.objects.create(
            name='Burpee',
            category='cardio',
            difficulty='advanced',
            equipment='Bodyweight',
            goal='weight_loss',
            default_reps=10, default_sets=4, duration_min=6, calories_per_set=15,
        )
        self.dead_bug = Exercise.objects.create(
            name='Dead Bug',
            category='core',
            difficulty='beginner',
            equipment='Bodyweight',
            goal='mobility',
            default_reps=10, default_sets=3, duration_min=3, calories_per_set=5,
        )

    def test_list_page_renders(self):
        resp = self.client.get(reverse('exercise-list'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Pull-Up')
        self.assertContains(resp, 'Burpee')
        self.assertContains(resp, 'Workout Library')

    def test_list_page_shows_recommended_for_calisthenics(self):
        user = User.objects.create_user('cali', 'cali@test.com', 'pw')
        Goal.objects.create(user=user, goal_type='calisthenics', focus_areas=[])
        self.client.login(username='cali', password='pw')

        resp = self.client.get(reverse('exercise-list'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'is-recommended')
        self.assertContains(resp, 'Recommended')

    def test_list_page_highlights_weight_loss_for_fat_loss_goal(self):
        user = User.objects.create_user('fat', 'fat@test.com', 'pw')
        Goal.objects.create(user=user, goal_type='fat_loss', focus_areas=[])
        self.client.login(username='fat', password='pw')

        resp = self.client.get(reverse('exercise-list'))
        self.assertTrue(resp.context['recommended_count'] >= 1)
        recommended = [e for e in resp.context['exercises'] if e['recommended']]
        self.assertTrue(any(e['name'] == 'Burpee' for e in recommended))

    def test_detail_page_renders(self):
        resp = self.client.get(reverse('exercise-detail', args=[self.pull_up.slug]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Pull-Up')

    def test_detail_page_shows_quick_complete_when_authenticated(self):
        user = User.objects.create_user('det', 'det@test.com', 'pw')
        self.client.login(username='det', password='pw')
        resp = self.client.get(reverse('exercise-detail', args=[self.pull_up.slug]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Mark Complete')

    def test_detail_requires_auth_for_quick_complete(self):
        resp = self.client.post(reverse('exercise-complete', args=[self.pull_up.slug]))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/users/login/', resp['Location'])


class QuickCompleteTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('logger', 'log@test.com', 'pw')
        self.exercise = Exercise.objects.create(
            name='Push-Up',
            category='chest',
            difficulty='beginner',
            equipment='Bodyweight',
            default_reps=15, default_sets=3, duration_min=4, calories_per_set=7,
        )

    def test_quick_complete_creates_completion(self):
        self.client.login(username='logger', password='pw')
        self.assertEqual(ExerciseCompletion.objects.count(), 0)
        resp = self.client.post(reverse('exercise-complete', args=[self.exercise.slug]))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(ExerciseCompletion.objects.count(), 1)
        completion = ExerciseCompletion.objects.first()
        self.assertEqual(completion.user, self.user)
        self.assertEqual(completion.exercise, self.exercise)
        self.assertEqual(completion.reps, 15)

    def test_quick_complete_updates_stats(self):
        from progress.models import UserWorkoutStats
        self.client.login(username='logger', password='pw')
        self.assertFalse(UserWorkoutStats.objects.filter(user=self.user).exists())
        self.client.post(reverse('exercise-complete', args=[self.exercise.slug]))
        stats = UserWorkoutStats.objects.get(user=self.user)
        self.assertEqual(stats.total_workouts, 1)
        self.assertEqual(stats.current_streak, 1)

    def test_quick_complete_redirects_to_records_when_next_set(self):
        self.client.login(username='logger', password='pw')
        resp = self.client.post(
            reverse('exercise-complete', args=[self.exercise.slug]),
            data={'next': reverse('exercise-records')},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], reverse('exercise-records'))

    def test_get_method_rejected(self):
        self.client.login(username='logger', password='pw')
        resp = self.client.get(reverse('exercise-complete', args=[self.exercise.slug]))
        self.assertEqual(resp.status_code, 405)
        self.assertEqual(ExerciseCompletion.objects.count(), 0)
