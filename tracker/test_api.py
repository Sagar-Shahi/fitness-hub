from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from accounts.models import ApiKey

from .models import BodyMetric, Meal, Workout
from .testutils import PASSWORD, days_ago, make_meal, make_user, make_weight, make_workout

WORKOUTS, MEALS, WEIGHT, SUMMARY = '/api/v1/workouts/', '/api/v1/meals/', '/api/v1/weight/', '/api/v1/summary/'


class ApiCase(TestCase):
    def setUp(self):
        cache.clear()
        self.user = make_user('sam')
        self.key, self.raw = ApiKey.issue(self.user, 'test')
        self.api = APIClient()
        self.api.credentials(HTTP_AUTHORIZATION=f'Bearer {self.raw}')

    def other(self, name='other'):
        user = make_user(name)
        _, raw = ApiKey.issue(user, 'k')
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {raw}')
        return user, client


class AuthTests(ApiCase):
    def test_every_endpoint_needs_credentials(self):
        for url in (WORKOUTS, MEALS, WEIGHT, SUMMARY, WORKOUTS + '1/'):
            with self.subTest(url=url):
                response = APIClient().get(url)
                self.assertEqual(response.status_code, 401)
                self.assertIn('Bearer', response['WWW-Authenticate'])

    def test_keys_have_the_fh_prefix_and_only_the_hash_is_stored(self):
        self.assertTrue(self.raw.startswith('fh_'))
        self.assertNotIn(self.raw, ApiKey.objects.get().key_hash)

    def test_wrong_and_revoked_keys(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer fh_' + 'a' * 43)
        self.assertEqual(client.get(WORKOUTS).json(), {'detail': 'Invalid API key.'})
        self.key.revoke()
        self.assertEqual(self.api.get(WORKOUTS).status_code, 401)

    def test_deactivated_accounts_lose_api_access(self):
        get_user_model().objects.filter(pk=self.user.pk).update(is_active=False)
        self.assertEqual(self.api.get(WORKOUTS).status_code, 401)

    def test_session_users_must_send_csrf(self):
        client = APIClient(enforce_csrf_checks=True)
        client.login(username='sam', password=PASSWORD)
        self.assertEqual(client.get(WORKOUTS).status_code, 200)
        self.assertEqual(client.post(MEALS, {'date': days_ago(0).isoformat(), 'name': 'x', 'calories': 1}, format='json').status_code, 403)
        self.assertEqual(Meal.objects.count(), 0)

    def test_json_only(self):
        self.assertEqual(self.api.get(WORKOUTS, HTTP_ACCEPT='text/html').status_code, 406)
        self.assertEqual(self.api.post(MEALS, {'name': 'x'}).status_code, 415)  # form-encoded body
        self.assertEqual(self.api.post(MEALS, 'not json', content_type='application/json').status_code, 400)

    @override_settings(API_RATE_USER='3/min')
    def test_throttling(self):
        self.assertEqual([self.api.get(SUMMARY).status_code for _ in range(5)], [200, 200, 200, 429, 429])
        _, other_client = self.other()
        self.assertEqual(other_client.get(SUMMARY).status_code, 200)


class WorkoutApiTests(ApiCase):
    BODY = {'date': None, 'name': 'Push day', 'duration_min': 55, 'notes': '',
            'exercises': [{'name': 'Bench press', 'sets': 4, 'reps': 8, 'weight_kg': '60'},
                          {'name': 'Dips', 'sets': 3, 'reps': 10, 'weight_kg': '0'}]}

    def body(self, **changes):
        return {**self.BODY, 'date': days_ago(0).isoformat(), **changes}

    def test_create_with_exercises_and_volume(self):
        response = self.api.post(WORKOUTS, self.body(), format='json')
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(len(data['exercises']), 2)
        self.assertEqual(Decimal(data['volume_kg']), Decimal('1920.0'))  # 4*8*60
        self.assertEqual(Workout.objects.get().owner, self.user)

    def test_server_owned_fields_cannot_be_set(self):
        other = make_user('victim')
        response = self.api.post(WORKOUTS, self.body(owner=other.pk, id=999, volume_kg='99999', created_at='2001-01-01T00:00:00Z'), format='json')
        self.assertEqual(response.status_code, 201)
        workout = Workout.objects.get()
        self.assertEqual(workout.owner, self.user)
        self.assertNotEqual(workout.pk, 999)
        self.assertGreater(workout.created_at.year, 2020)

    def test_bad_input(self):
        cases = [{'duration_min': 0}, {'duration_min': 601}, {'name': ''}, {'name': 'x' * 81}, {'date': 'yesterday'},
                 {'date': '2999-01-01'}, {'exercises': [{'name': 'x', 'sets': 0, 'reps': 1, 'weight_kg': 1}]},
                 {'exercises': [{'name': 'x', 'sets': 1, 'reps': 1, 'weight_kg': -5}]}, {'exercises': 'nope'}]
        for changes in cases:
            with self.subTest(changes=changes):
                self.assertEqual(self.api.post(WORKOUTS, self.body(**changes), format='json').status_code, 400)
        self.assertEqual(Workout.objects.count(), 0)

    @override_settings(MAX_EXERCISES_PER_WORKOUT=1)
    def test_exercise_limit(self):
        self.assertEqual(self.api.post(WORKOUTS, self.body(), format='json').status_code, 400)

    @override_settings(MAX_WORKOUTS_PER_USER=1)
    def test_workout_limit(self):
        self.assertEqual(self.api.post(WORKOUTS, self.body(), format='json').status_code, 201)
        self.assertEqual(self.api.post(WORKOUTS, self.body(), format='json').status_code, 400)

    def test_patch_keeps_exercises_unless_a_list_is_sent(self):
        wid = self.api.post(WORKOUTS, self.body(), format='json').json()['id']
        self.api.patch(f'{WORKOUTS}{wid}/', {'name': 'Renamed'}, format='json')
        workout = Workout.objects.get(pk=wid)
        self.assertEqual((workout.name, workout.exercises.count()), ('Renamed', 2))
        self.api.patch(f'{WORKOUTS}{wid}/', {'exercises': [{'name': 'Row', 'sets': 3, 'reps': 8, 'weight_kg': '50'}]}, format='json')
        self.assertEqual([e.name for e in workout.exercises.all()], ['Row'])

    def test_list_pagination_and_delete(self):
        for n in range(3):
            make_workout(self.user, ago=n)
        body = self.api.get(WORKOUTS, {'page_size': 2}).json()
        self.assertEqual((body['count'], len(body['results'])), (3, 2))
        self.assertEqual(self.api.get(WORKOUTS, {'page_size': 100000}).status_code, 200)
        wid = body['results'][0]['id']
        self.assertEqual(self.api.delete(f'{WORKOUTS}{wid}/').status_code, 204)
        self.assertEqual(Workout.objects.count(), 2)

    def test_other_users_workouts_are_invisible_and_untouchable(self):
        theirs = make_workout(make_user('victim'), name='THEIRS')
        self.assertEqual(self.api.get(WORKOUTS).json()['count'], 0)
        for call in (self.api.get, self.api.delete):
            self.assertEqual(call(f'{WORKOUTS}{theirs.pk}/').status_code, 404)
        self.assertEqual(self.api.patch(f'{WORKOUTS}{theirs.pk}/', {'name': 'hacked'}, format='json').status_code, 404)
        self.assertEqual(self.api.put(f'{WORKOUTS}{theirs.pk}/', self.body(), format='json').status_code, 404)
        theirs.refresh_from_db()
        self.assertEqual(theirs.name, 'THEIRS')


class MealApiTests(ApiCase):
    def test_create_filter_update_delete(self):
        body = {'date': days_ago(0).isoformat(), 'kind': 'lunch', 'name': 'Dal', 'calories': 600, 'protein_g': 20, 'carbs_g': 90, 'fat_g': 10}
        created = self.api.post(MEALS, body, format='json')
        self.assertEqual(created.status_code, 201)
        self.assertEqual(Meal.objects.get().owner, self.user)
        make_meal(self.user, ago=3, name='Old')
        self.assertEqual(self.api.get(MEALS).json()['count'], 2)
        self.assertEqual(self.api.get(MEALS, {'date': days_ago(0).isoformat()}).json()['count'], 1)
        self.assertEqual(self.api.get(MEALS, {'date': 'junk'}).status_code, 400)
        mid = created.json()['id']
        self.assertEqual(self.api.patch(f'{MEALS}{mid}/', {'calories': 650}, format='json').status_code, 200)
        self.assertEqual(Meal.objects.get(pk=mid).calories, 650)
        self.assertEqual(self.api.delete(f'{MEALS}{mid}/').status_code, 204)

    def test_bad_input_and_limits(self):
        good = {'date': days_ago(0).isoformat(), 'name': 'x', 'calories': 100}
        for changes in ({'calories': -1}, {'calories': 99999}, {'kind': 'brunch'}, {'name': ''}, {'date': '2999-01-01'}):
            with self.subTest(changes=changes):
                self.assertEqual(self.api.post(MEALS, dict(good, **changes), format='json').status_code, 400)
        with override_settings(MAX_MEALS_PER_DAY=1):
            self.assertEqual(self.api.post(MEALS, good, format='json').status_code, 201)
            self.assertEqual(self.api.post(MEALS, good, format='json').status_code, 400)

    def test_other_users_meals(self):
        theirs = make_meal(make_user('victim'))
        self.assertEqual(self.api.get(f'{MEALS}{theirs.pk}/').status_code, 404)
        self.assertEqual(self.api.delete(f'{MEALS}{theirs.pk}/').status_code, 404)
        self.assertEqual(Meal.objects.count(), 1)


class WeightApiTests(ApiCase):
    def test_posting_the_same_day_replaces_the_value(self):
        day = days_ago(0).isoformat()
        self.assertEqual(self.api.post(WEIGHT, {'date': day, 'weight_kg': '81.0'}, format='json').status_code, 201)
        self.assertEqual(self.api.post(WEIGHT, {'date': day, 'weight_kg': '80.4'}, format='json').status_code, 201)
        self.assertEqual(BodyMetric.objects.get().weight_kg, Decimal('80.4'))

    def test_bad_input(self):
        for body in ({'date': days_ago(0).isoformat(), 'weight_kg': '5'}, {'date': days_ago(0).isoformat(), 'weight_kg': '999'},
                     {'date': '2999-01-01', 'weight_kg': '80'}, {'weight_kg': '80'}, {'date': days_ago(0).isoformat()}):
            with self.subTest(body=body):
                self.assertEqual(self.api.post(WEIGHT, body, format='json').status_code, 400)

    def test_moving_an_entry_onto_another_day_is_refused(self):
        a, b = make_weight(self.user, ago=1), make_weight(self.user, ago=0)
        response = self.api.patch(f'{WEIGHT}{a.pk}/', {'date': b.date.isoformat()}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_other_users_entries(self):
        theirs = make_weight(make_user('victim'))
        self.assertEqual(self.api.get(f'{WEIGHT}{theirs.pk}/').status_code, 404)
        self.assertEqual(self.api.get(WEIGHT).json()['count'], 0)


class SummaryApiTests(ApiCase):
    def test_summary(self):
        make_workout(self.user, minutes=40)
        make_meal(self.user, calories=700, protein=40)
        make_weight(self.user, kg='79.9')
        data = self.api.get(SUMMARY).json()
        self.assertEqual((data['workouts_this_week'], data['minutes_this_week'], data['calories_today'], data['protein_g_today']), (1, 40, 700, 40))
        self.assertEqual((data['latest_weight_kg'], data['streak_days'], data['calorie_target']), ('79.9', 1, 2200))

    def test_summary_for_a_new_account(self):
        data = self.api.get(SUMMARY).json()
        self.assertEqual((data['workouts_this_week'], data['latest_weight_kg'], data['target_weight_kg']), (0, None, None))

    def test_summary_ignores_other_users(self):
        make_workout(make_user('other'))
        self.assertEqual(self.api.get(SUMMARY).json()['workouts_this_week'], 0)
