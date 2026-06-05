from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from exercises.models import Exercise, ExerciseCompletion


class WorkoutRecordsViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('recorder', 'r@test.com', 'pw')
        self.ex1 = Exercise.objects.create(
            name='Push-Up',
            category='chest',
            difficulty='beginner',
            equipment='Bodyweight',
            default_reps=15, default_sets=3, duration_min=4, calories_per_set=7,
        )
        self.ex2 = Exercise.objects.create(
            name='Plank',
            category='core',
            difficulty='beginner',
            equipment='Bodyweight',
            default_reps=1, default_sets=3, duration_min=3, calories_per_set=4,
        )
        self.completion1 = ExerciseCompletion.objects.create(
            user=self.user, exercise=self.ex1, reps=15,
        )
        self.completion2 = ExerciseCompletion.objects.create(
            user=self.user, exercise=self.ex2, reps=1,
        )

    def test_records_page_shows_real_completions(self):
        self.client.login(username='recorder', password='pw')
        resp = self.client.get(reverse('exercise-records'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Push-Up')
        self.assertContains(resp, 'Plank')
        self.assertContains(resp, 'Sessions')
        self.assertTrue(resp.context['has_records'])

    def test_records_page_empty_state(self):
        User.objects.create_user('empty', 'e@test.com', 'pw')
        self.client.login(username='empty', password='pw')
        resp = self.client.get(reverse('exercise-records'))
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.context['has_records'])
        self.assertContains(resp, 'No workouts logged yet')

    def test_records_summary_aggregates_totals(self):
        self.client.login(username='recorder', password='pw')
        resp = self.client.get(reverse('exercise-records'))
        summary = resp.context['summary']
        self.assertEqual(summary['total_completions'], 2)
        self.assertEqual(summary['total_sessions'], 1)
        self.assertEqual(summary['total_reps'], 16)
        self.assertEqual(summary['total_minutes'], 7)

    def test_records_requires_authentication(self):
        resp = self.client.get(reverse('exercise-records'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/users/login/', resp['Location'])


class SettingsViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='alice', email='alice@old.com', password='OldPass123!',
            first_name='Alice', last_name='Doe',
        )
        self.other = User.objects.create_user(
            username='bob', email='bob@x.com', password='BobPass123!',
        )

    def login(self):
        self.client.login(username='alice', password='OldPass123!')

    def test_settings_hub_requires_login(self):
        resp = self.client.get(reverse('settings-hub'))
        self.assertEqual(resp.status_code, 302)

    def test_settings_hub_renders(self):
        self.login()
        resp = self.client.get(reverse('settings-hub'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Settings')
        self.assertContains(resp, 'Account details')
        self.assertContains(resp, 'Change password')
        self.assertContains(resp, 'alice')

    def test_account_settings_page_renders(self):
        self.login()
        resp = self.client.get(reverse('settings-account'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Account details')
        self.assertContains(resp, 'name="username"')
        self.assertContains(resp, 'name="email"')

    def test_change_username(self):
        self.login()
        resp = self.client.post(reverse('settings-account'), {
            'username': 'alice2',
            'first_name': 'Alice',
            'last_name': 'Doe',
            'email': 'alice@old.com',
        }, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'alice2')

    def test_change_email(self):
        self.login()
        self.client.post(reverse('settings-account'), {
            'username': 'alice',
            'first_name': 'Alice',
            'last_name': 'Doe',
            'email': 'alice@new.com',
        })
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'alice@new.com')

    def test_username_uniqueness(self):
        self.login()
        resp = self.client.post(reverse('settings-account'), {
            'username': 'bob',
            'first_name': '', 'last_name': '',
            'email': 'alice@old.com',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'already taken')
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'alice')

    def test_email_uniqueness(self):
        self.login()
        resp = self.client.post(reverse('settings-account'), {
            'username': 'alice',
            'first_name': '', 'last_name': '',
            'email': 'bob@x.com',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'already registered')
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'alice@old.com')

    def test_username_required(self):
        self.login()
        resp = self.client.post(reverse('settings-account'), {
            'username': '',
            'first_name': '', 'last_name': '',
            'email': 'alice@old.com',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'required')

    def test_password_page_renders(self):
        self.login()
        resp = self.client.get(reverse('settings-password'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Change password')
        self.assertContains(resp, 'name="old_password"')
        self.assertContains(resp, 'name="new_password1"')
        self.assertContains(resp, 'name="new_password2"')

    def test_password_change_success(self):
        self.login()
        resp = self.client.post(reverse('settings-password'), {
            'old_password': 'OldPass123!',
            'new_password1': 'NewSecret456!',
            'new_password2': 'NewSecret456!',
        }, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewSecret456!'))
        self.assertFalse(self.user.check_password('OldPass123!'))

    def test_password_change_wrong_old(self):
        self.login()
        resp = self.client.post(reverse('settings-password'), {
            'old_password': 'wrongpassword',
            'new_password1': 'NewSecret456!',
            'new_password2': 'NewSecret456!',
        })
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('OldPass123!'))

    def test_password_change_mismatch(self):
        self.login()
        resp = self.client.post(reverse('settings-password'), {
            'old_password': 'OldPass123!',
            'new_password1': 'NewSecret456!',
            'new_password2': 'NewSecret789!',
        })
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('OldPass123!'))

    def test_password_change_keeps_session(self):
        self.login()
        self.client.post(reverse('settings-password'), {
            'old_password': 'OldPass123!',
            'new_password1': 'NewSecret456!',
            'new_password2': 'NewSecret456!',
        })
        # After password change the session is kept; we should still be logged in.
        resp = self.client.get(reverse('settings-hub'))
        self.assertEqual(resp.status_code, 200)

    def test_settings_hub_shows_email_pill(self):
        self.login()
        resp = self.client.get(reverse('settings-hub'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Email verified')
