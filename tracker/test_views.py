import re
import csv
import io
from unittest.mock import patch
from datetime import timedelta
from decimal import Decimal

from django.core.cache import cache, caches
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import BodyMetric, Exercise, ExerciseSet, Meal, Profile, Workout
from .testutils import days_ago, make_meal, make_user, make_weight, make_workout


class LoginRequiredTests(TestCase):
    def test_every_app_page_needs_a_login(self):
        owner = make_user('owner')
        workout, meal, weight = make_workout(owner), make_meal(owner), make_weight(owner)
        exercise = workout.exercises.first()
        urls = [
            reverse('tracker:dashboard'), reverse('tracker:share-progress'), reverse('tracker:focus-music-search'), reverse('tracker:goals'), reverse('tracker:workout-list'), reverse('tracker:workout-create'),
            reverse('tracker:exercise-library'),
            reverse('tracker:export'), reverse('tracker:weight'), reverse('tracker:meals'),
            reverse('tracker:workout-detail', args=[workout.pk]), reverse('tracker:workout-edit', args=[workout.pk]),
            reverse('tracker:workout-delete', args=[workout.pk]), reverse('tracker:exercise-add', args=[workout.pk]),
            reverse('tracker:exercise-delete', args=[workout.pk, exercise.pk]), reverse('tracker:weight-delete', args=[weight.pk]),
            reverse('tracker:meal-edit', args=[meal.pk]), reverse('tracker:meal-delete', args=[meal.pk]),
            reverse('shop:plans'), reverse('shop:cart'), reverse('shop:orders'), reverse('shop:my-plans'), reverse('shop:checkout'),
        ]
        for url in urls:
            for method in (self.client.get, self.client.post):
                with self.subTest(url=url, method=method.__name__):
                    response = method(url)
                    self.assertEqual(response.status_code, 302)
                    self.assertTrue(response['Location'].startswith(reverse('accounts:login')))
        self.assertEqual((Workout.objects.count(), Meal.objects.count(), BodyMetric.objects.count()), (1, 1, 1))


class Base(TestCase):
    def setUp(self):
        cache.clear()
        caches['research'].clear()
        self.user = make_user('sam')
        self.client.force_login(self.user)



class FocusMusicSearchTests(Base):
    def test_query_is_required_and_bounded(self):
        url = reverse('tracker:focus-music-search')
        for query in ('', 'x', 'x' * 101):
            with self.subTest(query=query):
                self.assertEqual(self.client.get(url, {'q': query}).status_code, 400)

    @patch.dict('os.environ', {'YOUTUBE_API_KEY': ''})
    def test_missing_api_key_has_a_safe_fallback_message(self):
        response = self.client.get(reverse('tracker:focus-music-search'), {'q': 'gym music'})
        self.assertEqual(response.status_code, 503)
        self.assertIn('paste a YouTube video link', response.json()['error'])

    @patch.dict('os.environ', {'YOUTUBE_API_KEY': 'test-key'})
    @patch('tracker.tutorials.urlopen')
    def test_returns_only_valid_embeddable_video_results(self, urlopen_mock):
        class FakeResponse:
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc_value, traceback):
                return False
            def read(self):
                return (
                    b'{"items":['
                    b'{"id":{"videoId":"abcdefghijk"},"snippet":{"title":"Gym mix","channelTitle":"Music","thumbnails":{"medium":{"url":"https://i.ytimg.com/vi/abcdefghijk/mqdefault.jpg"}}}},'
                    b'{"id":{"videoId":"bad"},"snippet":{"title":"Invalid"}}]}'
                )
        urlopen_mock.return_value = FakeResponse()
        response = self.client.get(reverse('tracker:focus-music-search'), {'q': 'gym music'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['videos']), 1)
        self.assertEqual(response.json()['videos'][0]['id'], 'abcdefghijk')
        self.assertEqual(response.json()['videos'][0]['title'], 'Gym mix')
        self.assertIn('videoEmbeddable=true', urlopen_mock.call_args.args[0].full_url)

    @override_settings(YOUTUBE_DAILY_SEARCH_LIMIT=1)
    @patch.dict('os.environ', {'YOUTUBE_API_KEY': 'test-key'})
    @patch('tracker.tutorials.urlopen')
    def test_daily_budget_also_limits_music_search(self, urlopen_mock):
        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self, exc_type, exc_value, traceback): return False
            def read(self):
                return b'{"items":[{"id":{"videoId":"abcdefghijk"},"snippet":{"title":"Gym mix"}}]}'
        urlopen_mock.return_value = FakeResponse()
        url = reverse('tracker:focus-music-search')
        first = self.client.get(url, {'q': 'gym music'})
        second = self.client.get(url, {'q': 'strength playlist'})
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 429)
        urlopen_mock.assert_called_once()

    @patch.dict('os.environ', {'YOUTUBE_API_KEY': 'test-key'})
    @patch('tracker.tutorials.urlopen')
    def test_cached_music_results_are_shared_and_do_not_need_a_key(self, urlopen_mock):
        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self, exc_type, exc_value, traceback): return False
            def read(self):
                return b'{"items":[{"id":{"videoId":"abcdefghijk"},"snippet":{"title":"Gym mix"}}]}'
        urlopen_mock.return_value = FakeResponse()
        url = reverse('tracker:focus-music-search')
        first = self.client.get(url, {'q': 'gym music'})
        other = make_user('music-search-other')
        self.client.force_login(other)
        with patch.dict('os.environ', {'YOUTUBE_API_KEY': ''}):
            second = self.client.get(url, {'q': ' gym   music '})
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.json(), first.json())
        urlopen_mock.assert_called_once()


class DashboardTests(Base):
    def test_empty_account_sees_a_welcome(self):
        response = self.client.get(reverse('tracker:dashboard'))
        self.assertContains(response, "Let's get your first numbers in")
        self.assertEqual(Profile.objects.filter(owner=self.user).count(), 1)

    def test_numbers_for_an_account_with_data(self):
        make_workout(self.user, name='Leg day')
        make_meal(self.user, calories=640)
        make_weight(self.user, kg='79.4')
        response = self.client.get(reverse('tracker:dashboard'))
        self.assertContains(response, 'Leg day')
        self.assertContains(response, '640')
        self.assertContains(response, '79.4 kg')
        self.assertContains(response, '<svg class="chart-svg"')
        self.assertNotContains(response, "Let's get your first numbers in")

    def test_only_my_data_is_shown(self):
        other = make_user('other')
        make_workout(other, name='OTHERS-SECRET-WORKOUT')
        self.assertNotContains(self.client.get(reverse('tracker:dashboard')), 'OTHERS-SECRET-WORKOUT')

    def test_the_period_is_validated(self):
        for junk in ('abc', '1', '-5', '9999', ''):
            with self.subTest(days=junk):
                self.assertEqual(self.client.get(reverse('tracker:dashboard'), {'days': junk}).context['days'], 30)
        self.assertEqual(self.client.get(reverse('tracker:dashboard'), {'days': '7'}).context['days'], 7)



class ShareProgressTests(Base):
    def test_summary_only_counts_the_signed_in_users_last_30_days(self):
        make_workout(self.user, name='My workout')
        other = make_user('another')
        make_workout(other, name='Private other workout')
        response = self.client.get(reverse('tracker:share-progress'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['workouts'], 1)
        self.assertEqual(response.context['completed_sets'], 4)
        self.assertContains(response, 'Share your progress')
        self.assertNotContains(response, 'Private other workout')

    def test_summary_is_empty_for_a_new_account(self):
        response = self.client.get(reverse('tracker:share-progress'))
        self.assertEqual(response.context['workouts'], 0)
        self.assertEqual(response.context['completed_sets'], 0)


class GoalsTests(Base):
    def test_save_goals(self):
        response = self.client.post(reverse('tracker:goals'), {'calorie_target': 1900, 'weekly_workout_target': 5, 'target_weight_kg': '75.5'})
        self.assertRedirects(response, reverse('tracker:dashboard'))
        profile = Profile.objects.get(owner=self.user)
        self.assertEqual((profile.calorie_target, profile.weekly_workout_target, profile.target_weight_kg), (1900, 5, Decimal('75.5')))

    def test_unreasonable_goals_are_refused(self):
        for data in ({'calorie_target': 100, 'weekly_workout_target': 3}, {'calorie_target': 2000, 'weekly_workout_target': 0},
                     {'calorie_target': 2000, 'weekly_workout_target': 20}, {'calorie_target': 2000, 'weekly_workout_target': 3, 'target_weight_kg': '5'},
                     {'calorie_target': 99999, 'weekly_workout_target': 3}):
            with self.subTest(data=data):
                self.assertEqual(self.client.post(reverse('tracker:goals'), data).status_code, 200)

    def test_goals_are_per_user(self):
        other = make_user('other')
        Profile.objects.create(owner=other, calorie_target=3000)
        self.client.post(reverse('tracker:goals'), {'calorie_target': 1800, 'weekly_workout_target': 2})
        self.assertEqual(Profile.objects.get(owner=other).calorie_target, 3000)


class WorkoutTests(Base):
    DATA = {'name': 'Push day', 'date': '', 'duration_min': 50, 'notes': 'felt strong'}

    def _post(self, **changes):
        data = {**self.DATA, 'date': days_ago(0).isoformat(), **changes}
        return self.client.post(reverse('tracker:workout-create'), data)

    def test_create(self):
        response = self._post()
        workout = Workout.objects.get()
        self.assertRedirects(response, reverse('tracker:workout-detail', args=[workout.pk]))
        self.assertEqual((workout.owner, workout.name, workout.duration_min), (self.user, 'Push day', 50))

    def test_bad_input_is_refused(self):
        for changes in ({'duration_min': 0}, {'duration_min': 601}, {'duration_min': 'x'}, {'name': ''}, {'name': 'x' * 81},
                        {'date': (days_ago(0) + timedelta(days=2)).isoformat()}, {'date': 'not-a-date'}, {'notes': 'x' * 501}):
            with self.subTest(changes=changes):
                self.assertEqual(self._post(**changes).status_code, 200)
        self.assertEqual(Workout.objects.count(), 0)

    def test_owner_cannot_be_set_from_the_form(self):
        other = make_user('other')
        self._post(owner=other.pk)
        self.assertEqual(Workout.objects.get().owner, self.user)

    @override_settings(MAX_WORKOUTS_PER_USER=2)
    def test_workout_limit(self):
        self._post(); self._post()
        self.assertContains(self._post(), 'limit of 2 workouts')
        self.assertEqual(Workout.objects.count(), 2)

    def test_edit_and_delete(self):
        workout = make_workout(self.user)
        data = dict(self.DATA, date=days_ago(1).isoformat(), name='Renamed')
        self.assertRedirects(self.client.post(reverse('tracker:workout-edit', args=[workout.pk]), data),
                             reverse('tracker:workout-detail', args=[workout.pk]))
        workout.refresh_from_db()
        self.assertEqual((workout.name, workout.date), ('Renamed', days_ago(1)))
        url = reverse('tracker:workout-delete', args=[workout.pk])
        self.assertContains(self.client.get(url), 'Delete this workout?')
        self.assertTrue(Workout.objects.exists())
        self.assertRedirects(self.client.post(url), reverse('tracker:workout-list'))
        self.assertEqual((Workout.objects.count(), Exercise.objects.count()), (0, 0))

    def test_detail_shows_volume(self):
        workout = make_workout(self.user, exercises=(('Squat', 4, 5, '100'), ('Row', 3, 10, '50.5')))
        response = self.client.get(reverse('tracker:workout-detail', args=[workout.pk]))
        self.assertContains(response, 'Squat')
        self.assertContains(response, '3515 kg')  # 4x5x100 + 3x10x50.5


class ExerciseTests(Base):
    def setUp(self):
        super().setUp()
        self.workout = make_workout(self.user, exercises=())
        self.url = reverse('tracker:exercise-add', args=[self.workout.pk])

    def test_add_and_remove(self):
        response = self.client.post(self.url, {'name': 'Deadlift', 'sets': 3, 'reps': 5, 'weight_kg': '120.5'})
        self.assertRedirects(response, reverse('tracker:workout-detail', args=[self.workout.pk]))
        exercise = self.workout.exercises.get()
        self.assertEqual((exercise.name, exercise.weight_kg), ('Deadlift', Decimal('120.5')))
        self.client.post(reverse('tracker:exercise-delete', args=[self.workout.pk, exercise.pk]))
        self.assertEqual(self.workout.exercises.count(), 0)

    def test_bad_values_are_refused(self):
        for data in ({'name': 'x', 'sets': 0, 'reps': 5, 'weight_kg': 10}, {'name': 'x', 'sets': 3, 'reps': 0, 'weight_kg': 10},
                     {'name': 'x', 'sets': 51, 'reps': 5, 'weight_kg': 10}, {'name': 'x', 'sets': 3, 'reps': 5, 'weight_kg': -1},
                     {'name': 'x', 'sets': 3, 'reps': 5, 'weight_kg': 5000}, {'name': '', 'sets': 3, 'reps': 5, 'weight_kg': 10}):
            with self.subTest(data=data):
                self.assertEqual(self.client.post(self.url, data).status_code, 400)
        self.assertEqual(self.workout.exercises.count(), 0)

    @override_settings(MAX_EXERCISES_PER_WORKOUT=2)
    def test_exercise_limit(self):
        for _ in range(2):
            self.client.post(self.url, {'name': 'x', 'sets': 3, 'reps': 5, 'weight_kg': 10})
        self.assertEqual(self.client.post(self.url, {'name': 'x', 'sets': 3, 'reps': 5, 'weight_kg': 10}).status_code, 400)
        self.assertEqual(self.workout.exercises.count(), 2)

    def test_get_is_not_allowed_for_changes(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)


class ExerciseSetTests(Base):
    def setUp(self):
        super().setUp()
        self.workout = make_workout(self.user, exercises=())
        self.exercise = Exercise.objects.create(
            workout=self.workout, name='Bench press', sets=2, reps=10, weight_kg=Decimal('40.0')
        )
        self.first = ExerciseSet.objects.create(
            exercise=self.exercise, set_number=1, reps=10, weight_kg=Decimal('40.0')
        )
        self.second = ExerciseSet.objects.create(
            exercise=self.exercise, set_number=2, reps=8, weight_kg=Decimal('50.0')
        )

    def test_set_forms_have_unique_accessible_field_ids(self):
        workout = make_workout(
            self.user,
            exercises=(('Squat', 2, 8, '60'), ('Row', 2, 10, '40')),
        )
        response = self.client.get(reverse('tracker:workout-detail', args=[workout.pk]))
        ids = re.findall(r'\bid="([^"]+)"', response.content.decode())
        self.assertEqual(len(ids), len(set(ids)))

    def test_completed_set_volume(self):
        self.assertEqual(self.workout.volume_kg, Decimal('0'))
        self.first.is_completed = True
        self.first.save()
        self.assertEqual(self.workout.volume_kg, Decimal('400.0'))
        self.second.is_completed = True
        self.second.save()
        self.assertEqual(self.workout.volume_kg, Decimal('800.0'))

    def test_add_edit_and_delete_sets(self):
        add_url = reverse('tracker:exercise-set-add', args=[self.workout.pk, self.exercise.pk])
        response = self.client.post(add_url, {'add-set-' + str(self.exercise.pk) + '-reps': 6, 'add-set-' + str(self.exercise.pk) + '-weight_kg': '60.0', 'add-set-' + str(self.exercise.pk) + '-is_warmup': False})
        self.assertRedirects(response, reverse('tracker:workout-detail', args=[self.workout.pk]))
        third = self.exercise.set_entries.get(set_number=3)
        self.assertEqual((third.reps, third.weight_kg, third.is_completed), (6, Decimal('60.0'), False))

        edit_url = reverse('tracker:exercise-set-edit', args=[self.workout.pk, self.exercise.pk, third.pk])
        response = self.client.post(edit_url, {
            f'set-{third.pk}-reps': 5, f'set-{third.pk}-weight_kg': '65.0',
            f'set-{third.pk}-is_warmup': False, f'set-{third.pk}-is_completed': True,
        })
        self.assertRedirects(response, reverse('tracker:workout-detail', args=[self.workout.pk]))
        third.refresh_from_db()
        self.assertEqual((third.reps, third.weight_kg, third.is_completed), (5, Decimal('65.0'), True))

        delete_url = reverse('tracker:exercise-set-delete', args=[self.workout.pk, self.exercise.pk, self.second.pk])
        self.client.post(delete_url)
        self.assertEqual(list(self.exercise.set_entries.values_list('set_number', flat=True)), [1, 2])

    def test_deleting_first_set_renumbers_remaining_sets_without_unique_collision(self):
        third = ExerciseSet.objects.create(
            exercise=self.exercise, set_number=3, reps=6, weight_kg=Decimal('60.0')
        )
        delete_url = reverse('tracker:exercise-set-delete', args=[self.workout.pk, self.exercise.pk, self.first.pk])
        response = self.client.post(delete_url)
        self.assertRedirects(response, reverse('tracker:workout-detail', args=[self.workout.pk]))
        self.assertEqual(
            list(self.exercise.set_entries.values_list('set_number', flat=True)),
            [1, 2],
        )
        third.refresh_from_db()
        self.assertEqual(third.set_number, 2)

    def test_invalid_set_edit_preserves_session_progress_context(self):
        self.first.is_completed = True
        self.first.save(update_fields=['is_completed'])
        url = reverse('tracker:exercise-set-edit', args=[self.workout.pk, self.exercise.pk, self.second.pk])
        response = self.client.post(url, {
            f'set-{self.second.pk}-reps': 'not-a-number',
            f'set-{self.second.pk}-weight_kg': '50.0',
            f'set-{self.second.pk}-is_warmup': False,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.context['total_sets'], 2)
        self.assertEqual(response.context['completed_sets'], 1)
        self.assertEqual(response.context['progress_percent'], 50)

    def test_set_endpoints_are_post_only_and_owner_scoped(self):
        edit_url = reverse('tracker:exercise-set-edit', args=[self.workout.pk, self.exercise.pk, self.first.pk])
        self.assertEqual(self.client.get(edit_url).status_code, 405)
        other = make_user('other')
        other_workout = make_workout(other, exercises=())
        other_exercise = Exercise.objects.create(
            workout=other_workout, name='Private lift', sets=1, reps=1, weight_kg=Decimal('10.0')
        )
        other_set = ExerciseSet.objects.create(
            exercise=other_exercise, set_number=1, reps=1, weight_kg=Decimal('10.0')
        )
        foreign_url = reverse('tracker:exercise-set-edit', args=[self.workout.pk, self.exercise.pk, other_set.pk])
        self.assertEqual(self.client.post(foreign_url, {
            'reps': 1, 'weight_kg': '1.0', 'is_warmup': False, 'is_completed': True,
        }).status_code, 404)


class WeightTests(Base):
    def test_log_and_replace_same_day(self):
        url = reverse('tracker:weight')
        self.client.post(url, {'date': days_ago(0).isoformat(), 'weight_kg': '81.2'})
        self.client.post(url, {'date': days_ago(0).isoformat(), 'weight_kg': '80.9'})
        entry = BodyMetric.objects.get()
        self.assertEqual(entry.weight_kg, Decimal('80.9'))

    def test_bad_values_and_future_dates(self):
        url = reverse('tracker:weight')
        for data in ({'weight_kg': '5'}, {'weight_kg': '999'}, {'weight_kg': 'abc'}, {'weight_kg': ''},
                     {'weight_kg': '80', 'date': (days_ago(0) + timedelta(days=1)).isoformat()}):
            with self.subTest(data=data):
                self.assertEqual(self.client.post(url, dict({'date': days_ago(0).isoformat()}, **data)).status_code, 200)
        self.assertEqual(BodyMetric.objects.count(), 0)

    def test_deleting_latest_weight_recalculates_nutrition_from_previous_entry(self):
        profile = Profile.objects.create(
            owner=self.user, age=30, height_cm=180, starting_weight_kg=80,
            sex_for_calculation='male', activity_level='moderate',
            training_type='strength', nutrition_goal='maintain',
        )
        previous = make_weight(self.user, ago=1, kg='70.0')
        latest = make_weight(self.user, ago=0, kg='90.0')
        from .nutrition import calculate_nutrition_targets
        profile.calorie_target = calculate_nutrition_targets(profile, latest.weight_kg)['calories']
        profile.save(update_fields=['calorie_target'])
        response = self.client.post(reverse('tracker:weight-delete', args=[latest.pk]))
        self.assertRedirects(response, reverse('tracker:weight'))
        profile.refresh_from_db()
        expected = calculate_nutrition_targets(profile, previous.weight_kg)['calories']
        self.assertEqual(profile.calorie_target, expected)

    def test_same_date_for_two_users_is_fine(self):
        other = make_user('other')
        make_weight(other, kg='70.0')
        self.client.post(reverse('tracker:weight'), {'date': days_ago(0).isoformat(), 'weight_kg': '81'})
        self.assertEqual(BodyMetric.objects.get(owner=other).weight_kg, Decimal('70.0'))
        self.assertEqual(BodyMetric.objects.count(), 2)

    def test_delete_needs_post(self):
        entry = make_weight(self.user)
        url = reverse('tracker:weight-delete', args=[entry.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.post(url)
        self.assertEqual(BodyMetric.objects.count(), 0)


class MealTests(Base):
    DATA = {'name': 'Dal and rice', 'kind': 'lunch', 'calories': 650, 'protein_g': 24, 'carbs_g': 100, 'fat_g': 12}

    def _post(self, **changes):
        return self.client.post(reverse('tracker:meals'), {**self.DATA, 'date': days_ago(0).isoformat(), **changes})

    def test_log_and_totals(self):
        self.assertEqual(self._post().status_code, 302)
        self._post(name='Snack', calories=200, protein_g=5, carbs_g=30, fat_g=4)
        response = self.client.get(reverse('tracker:meals'))
        self.assertEqual(response.context['totals']['calories'], 850)
        self.assertContains(response, 'Dal and rice')

    def test_meal_page_offers_private_food_lookup_and_manual_entry(self):
        response = self.client.get(reverse('tracker:meals'))
        self.assertContains(response, 'id="food-search"')
        self.assertContains(response, 'data/food-catalog.json')
        self.assertContains(response, 'Searches stay in your browser.')
        self.assertContains(response, 'name="calories"')

    def test_bad_input(self):
        for changes in ({'calories': -1}, {'calories': 5001}, {'calories': ''}, {'kind': 'brunch'}, {'protein_g': 501}, {'name': ''},
                        {'date': (days_ago(0) + timedelta(days=1)).isoformat()}):
            with self.subTest(changes=changes):
                self.assertEqual(self._post(**changes).status_code, 200)
        self.assertEqual(Meal.objects.count(), 0)

    @override_settings(MAX_MEALS_PER_DAY=2)
    def test_daily_limit(self):
        self._post(); self._post()
        self.assertContains(self._post(), 'at most 2 meals per day')

    def test_other_days_and_bad_date_parameter(self):
        make_meal(self.user, ago=3, name='OLD-MEAL')
        day = days_ago(3).isoformat()
        self.assertContains(self.client.get(reverse('tracker:meals'), {'date': day}), 'OLD-MEAL')
        self.assertNotContains(self.client.get(reverse('tracker:meals')), 'OLD-MEAL')
        for junk in ('junk', '2026-13-45', "'; DROP TABLE", '9999-01-01'):
            with self.subTest(date=junk):
                self.assertEqual(self.client.get(reverse('tracker:meals'), {'date': junk}).status_code, 200)

    def test_edit_meal_updates_values_and_returns_to_the_updated_day(self):
        meal = make_meal(self.user, ago=2, name='Old meal')
        new_day = days_ago(1)
        response = self.client.post(reverse('tracker:meal-edit', args=[meal.pk]), {
            'name': 'Updated meal', 'kind': 'dinner', 'date': new_day.isoformat(),
            'calories': 720, 'protein_g': 35, 'carbs_g': 80, 'fat_g': 20,
        })
        self.assertRedirects(response, f"{reverse('tracker:meals')}?date={new_day.isoformat()}")
        meal.refresh_from_db()
        self.assertEqual((meal.name, meal.kind, meal.calories), ('Updated meal', 'dinner', 720))

    @override_settings(MAX_MEALS_PER_DAY=1)
    def test_editing_existing_meal_does_not_count_it_again(self):
        meal = make_meal(self.user, name='Existing meal')
        response = self.client.post(reverse('tracker:meal-edit', args=[meal.pk]), {
            'name': 'Still one meal', 'kind': 'lunch', 'date': days_ago(0).isoformat(),
            'calories': 500, 'protein_g': 20, 'carbs_g': 60, 'fat_g': 10,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Meal.objects.filter(owner=self.user).count(), 1)

    def test_cannot_edit_another_users_meal(self):
        other = make_user('meal-owner')
        meal = make_meal(other)
        self.assertEqual(self.client.get(reverse('tracker:meal-edit', args=[meal.pk])).status_code, 404)

    def test_delete_returns_to_the_same_day(self):
        meal = make_meal(self.user, ago=2)
        response = self.client.post(reverse('tracker:meal-delete', args=[meal.pk]))
        self.assertRedirects(response, f"{reverse('tracker:meals')}?date={days_ago(2).isoformat()}")
        self.assertEqual(Meal.objects.count(), 0)


class OwnershipTests(Base):
    """One user must never see or change another user's records, whatever the address says."""

    def setUp(self):
        super().setUp()
        self.other = make_user('other')
        self.workout = make_workout(self.other, name='THEIR-WORKOUT')
        self.meal = make_meal(self.other, name='THEIR-MEAL')
        self.weight = make_weight(self.other)

    def test_other_users_workout_pages_are_404(self):
        exercise = self.workout.exercises.first()
        checks = [
            (self.client.get, reverse('tracker:workout-detail', args=[self.workout.pk])),
            (self.client.get, reverse('tracker:workout-edit', args=[self.workout.pk])),
            (self.client.post, reverse('tracker:workout-edit', args=[self.workout.pk])),
            (self.client.get, reverse('tracker:workout-delete', args=[self.workout.pk])),
            (self.client.post, reverse('tracker:workout-delete', args=[self.workout.pk])),
            (self.client.post, reverse('tracker:exercise-add', args=[self.workout.pk])),
            (self.client.post, reverse('tracker:exercise-delete', args=[self.workout.pk, exercise.pk])),
        ]
        for method, url in checks:
            with self.subTest(url=url, method=method.__name__):
                self.assertEqual(method(url, {'name': 'hacked', 'sets': 1, 'reps': 1, 'weight_kg': 1, 'duration_min': 1, 'date': '2026-01-01'}).status_code, 404)
        self.workout.refresh_from_db()
        self.assertEqual((self.workout.name, self.workout.exercises.count()), ('THEIR-WORKOUT', 1))

    def test_an_exercise_cannot_be_deleted_through_my_own_workout(self):
        mine = make_workout(self.user, exercises=())
        theirs = self.workout.exercises.first()
        self.assertEqual(self.client.post(reverse('tracker:exercise-delete', args=[mine.pk, theirs.pk])).status_code, 404)
        self.assertEqual(self.workout.exercises.count(), 1)

    def test_other_users_meals_and_weights_cannot_be_deleted(self):
        self.assertEqual(self.client.post(reverse('tracker:meal-delete', args=[self.meal.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('tracker:weight-delete', args=[self.weight.pk])).status_code, 404)
        self.assertEqual((Meal.objects.count(), BodyMetric.objects.count()), (1, 1))

    def test_other_users_data_never_appears_in_lists_or_export(self):
        for url in (reverse('tracker:workout-list'), reverse('tracker:meals'), reverse('tracker:weight'),
                    reverse('tracker:dashboard'), reverse('tracker:export')):
            self.assertNotContains(self.client.get(url), 'THEIR-')


class EscapingTests(Base):
    PAYLOAD = '<script>alert("xss")</script>'

    def test_user_text_is_escaped_everywhere(self):
        workout = make_workout(self.user, name=self.PAYLOAD)
        make_meal(self.user, name=self.PAYLOAD)
        for url in (reverse('tracker:workout-list'), reverse('tracker:workout-detail', args=[workout.pk]),
                    reverse('tracker:workout-edit', args=[workout.pk]), reverse('tracker:workout-delete', args=[workout.pk]),
                    reverse('tracker:meals'), reverse('tracker:dashboard')):
            with self.subTest(url=url):
                self.assertNotContains(self.client.get(url), self.PAYLOAD)


class ExportTests(Base):
    def test_export_rows_and_formula_defence(self):
        make_workout(self.user, name='=HYPERLINK("http://evil.example","x")', exercises=(('@SUM(A1)', 3, 5, '10'),))
        make_workout(self.user, name='Empty', exercises=())
        response = self.client.get(reverse('tracker:export'))
        self.assertTrue(response['Content-Type'].startswith('text/csv'))
        rows = list(csv.DictReader(io.StringIO(response.content.decode())))
        self.assertEqual(len(rows), 4)  # three individual sets plus the empty workout row
        formula = next(r for r in rows if r['minutes'] == '45' and r['set_number'] == '1')
        self.assertEqual([r['set_number'] for r in rows if r['exercise'] == "'@SUM(A1)"], ['1', '2', '3'])
        self.assertEqual(formula['is_completed'], 'True')
        self.assertTrue(formula['workout'].startswith("'"))
        self.assertTrue(formula['exercise'].startswith("'"))


class ExerciseLibraryTests(Base):
    EXERCISES = [
        {
            "name": "Dumbbell Curl", "level": "beginner", "category": "strength",
            "equipment": "dumbbell", "primaryMuscles": ["biceps"],
            "secondaryMuscles": ["forearms"], "instructions": ["Curl the weight."],
            "mechanic": "isolation", "id": "Dumbbell_Curl",
            "images": ["Dumbbell_Curl/0.jpg", "Dumbbell_Curl/1.jpg"],
        },
        {
            "name": "Barbell Squat", "level": "intermediate", "category": "strength",
            "equipment": "barbell", "primaryMuscles": ["quadriceps"],
            "secondaryMuscles": ["glutes"], "instructions": ["Squat with control."],
            "mechanic": "compound",
        },
        {
            "name": "Hamstring Stretch", "level": "beginner", "category": "stretching",
            "equipment": "body only", "primaryMuscles": ["hamstrings"],
            "secondaryMuscles": ["calves"], "instructions": ["Stretch gently."],
            "mechanic": None,
        },
    ]

    @patch("tracker.library._catalog", return_value=(EXERCISES, None))
    def test_exercise_cards_include_catalogue_images_and_safe_fallback(self, catalog):
        response = self.client.get(reverse("tracker:exercise-library"))
        self.assertEqual(
            response.context["exercises"][0]["image_url"],
            "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/Dumbbell_Curl/0.jpg",
        )
        self.assertEqual(response.context["exercises"][1]["image_url"], "")
        self.assertContains(response, 'class="library-exercise-image"')
        self.assertContains(response, "Movement guide")

    @patch("tracker.library._catalog", return_value=(EXERCISES, None))
    def test_search_includes_secondary_muscles(self, catalog):
        response = self.client.get(reverse("tracker:exercise-library"), {"q": "forearms"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["name"] for item in response.context["exercises"]], ["Dumbbell Curl"])

    @patch("tracker.library._catalog", return_value=(EXERCISES, None))
    def test_filters_by_level_and_movement_type(self, catalog):
        response = self.client.get(reverse("tracker:exercise-library"), {
            "level": "beginner", "category": "stretching",
        })
        self.assertEqual([item["name"] for item in response.context["exercises"]], ["Hamstring Stretch"])
        self.assertEqual(response.context["level"], "beginner")
        self.assertEqual(response.context["category"], "stretching")

    @patch("tracker.library._catalog", return_value=(EXERCISES, None))
    def test_invalid_page_numbers_clamp_to_a_valid_page(self, catalog):
        response = self.client.get(reverse("tracker:exercise-library"), {"page": "999999"})
        self.assertEqual(response.context["page"], response.context["page_count"])
        huge = self.client.get(reverse("tracker:exercise-library"), {"page": "9" * 5000})
        self.assertEqual(huge.status_code, 200)
        self.assertEqual(huge.context["page"], 1)

    @patch("tracker.library._catalog", return_value=(EXERCISES, None))
    def test_only_my_workouts_can_be_selected_for_quick_add(self, catalog):
        mine = make_workout(self.user, name="My workout", exercises=())
        other = make_user("other")
        theirs = make_workout(other, name="Private workout", exercises=())
        response = self.client.get(reverse("tracker:exercise-library"), {"workout": theirs.pk})
        self.assertIsNone(response.context["selected_workout"])
        self.assertEqual(list(response.context["workouts"]), [mine])
