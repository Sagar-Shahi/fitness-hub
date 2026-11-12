from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from tracker.testutils import PASSWORD, make_user

from .models import KEY_PREFIX, ApiKey, hash_key

User = get_user_model()

REGISTER = {
    'username': 'NewPerson', 'email': 'new@example.com',
    'password1': 'Another-Strong-Pass-77', 'password2': 'Another-Strong-Pass-77', 'website': '',
}


class RegistrationTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_registering_creates_a_hashed_account_and_logs_in(self):
        response = self.client.post(reverse('accounts:register'), REGISTER)
        self.assertRedirects(response, reverse('tracker:goals'))
        user = User.objects.get(username='NewPerson')
        self.assertEqual(user.email, 'new@example.com')
        self.assertNotIn('Another-Strong-Pass-77', user.password)
        self.assertTrue(user.check_password('Another-Strong-Pass-77'))
        self.assertIn('_auth_user_id', self.client.session)

    def test_the_hidden_bot_trap_blocks_sign_ups(self):
        response = self.client.post(reverse('accounts:register'), dict(REGISTER, website='http://spam.example'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.exists())

    def test_usernames_and_emails_are_unique_ignoring_case(self):
        make_user('taken')
        for field, value in (('username', 'TAKEN'), ('email', 'TAKEN@EXAMPLE.COM')):
            with self.subTest(field=field):
                data = dict(REGISTER, **{field: value})
                response = self.client.post(reverse('accounts:register'), data)
                self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 1)

    def test_weak_passwords_are_refused(self):
        for password in ('short1A', 'password1234', '1234567890123', 'newperson2026'):
            with self.subTest(password=password):
                data = dict(REGISTER, password1=password, password2=password)
                self.assertEqual(self.client.post(reverse('accounts:register'), data).status_code, 200)
        self.assertFalse(User.objects.exists())

    def test_mismatched_passwords_are_refused(self):
        self.client.post(reverse('accounts:register'), dict(REGISTER, password2='Different-Pass-12345'))
        self.assertFalse(User.objects.exists())

    @override_settings(REGISTER_MAX_PER_HOUR=2)
    def test_too_many_sign_up_attempts_from_one_address_are_slowed_down(self):
        statuses = [self.client.post(reverse('accounts:register'), dict(REGISTER, website='x')).status_code for _ in range(3)]
        self.assertEqual(statuses, [200, 200, 429])

    def test_signed_in_users_are_sent_to_the_dashboard(self):
        self.client.force_login(make_user())
        self.assertRedirects(self.client.get(reverse('accounts:register')), reverse('tracker:dashboard'))


class LoginTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = make_user('JohnDoe')
        self.url = reverse('accounts:login')

    def _login(self, username='JohnDoe', password=PASSWORD, **extra):
        return self.client.post(self.url, {'username': username, 'password': password}, **extra)

    def test_login_with_the_right_password(self):
        self.assertRedirects(self._login(), reverse('tracker:dashboard'))
        self.assertIn('_auth_user_id', self.client.session)

    def test_the_username_is_not_case_sensitive(self):
        self.assertEqual(self._login('johndoe').status_code, 302)
        self.assertIn('_auth_user_id', self.client.session)

    def test_a_wrong_password_fails(self):
        self.assertEqual(self._login(password='wrong-pass-123').status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    @override_settings(LOGIN_MAX_FAILURES=3)
    def test_after_too_many_failures_even_the_right_password_is_refused(self):
        for _ in range(3):
            self._login(password='wrong-pass-123')
        response = self._login()
        self.assertEqual(response.status_code, 429)
        self.assertContains(response, 'Too many failed login attempts', status_code=429)
        self.assertNotIn('_auth_user_id', self.client.session)

    @override_settings(LOGIN_MAX_FAILURES=3)
    def test_the_lockout_covers_every_spelling_of_the_username(self):
        for name in ('johndoe', 'JOHNDOE', 'JohnDoe'):
            self._login(name, 'wrong-pass-123')
        self.assertEqual(self._login('johndoe').status_code, 429)

    @override_settings(LOGIN_MAX_FAILURES=3)
    def test_other_usernames_and_other_addresses_are_not_affected(self):
        make_user('someone')
        for _ in range(3):
            self._login(password='wrong-pass-123')
        self.assertEqual(self._login('someone').status_code, 302)
        self.client.logout()
        self.assertEqual(self._login(REMOTE_ADDR='203.0.113.77').status_code, 302)

    @override_settings(LOGIN_MAX_FAILURES=3)
    def test_a_successful_login_resets_the_counter(self):
        for _ in range(2):
            self._login(password='wrong-pass-123')
        self._login()
        self.client.post(reverse('accounts:logout'))
        for _ in range(2):
            self._login(password='wrong-pass-123')
        self.assertEqual(self._login().status_code, 302)

    def test_login_will_not_redirect_to_another_website(self):
        response = self.client.post(self.url + '?next=//evil.example/steal', {'username': 'JohnDoe', 'password': PASSWORD})
        self.assertRedirects(response, reverse('tracker:dashboard'))

    def test_login_follows_a_safe_next_address(self):
        response = self.client.post(self.url + '?next=/app/workouts/', {'username': 'JohnDoe', 'password': PASSWORD})
        self.assertRedirects(response, reverse('tracker:workout-list'))

    def test_logout_needs_a_post(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('accounts:logout')).status_code, 405)
        self.assertIn('_auth_user_id', self.client.session)
        self.client.post(reverse('accounts:logout'))
        self.assertNotIn('_auth_user_id', self.client.session)


class PasswordChangeTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.url = reverse('accounts:password-change')

    def test_needs_login(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)

    def test_changing_the_password_keeps_the_session(self):
        self.client.force_login(self.user)
        new = 'Brand-New-Passphrase-42'
        response = self.client.post(self.url, {'old_password': PASSWORD, 'new_password1': new, 'new_password2': new})
        self.assertRedirects(response, self.url)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new))
        self.assertEqual(self.client.get(reverse('tracker:dashboard')).status_code, 200)

    def test_the_old_password_has_to_be_right(self):
        self.client.force_login(self.user)
        new = 'Brand-New-Passphrase-42'
        response = self.client.post(self.url, {'old_password': 'not-my-password', 'new_password1': new, 'new_password2': new})
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(PASSWORD))


class ApiKeyModelTests(TestCase):
    def test_issue_returns_the_raw_key_once_and_stores_only_a_hash(self):
        user = make_user()
        key, raw = ApiKey.issue(user, 'Zapier')
        self.assertTrue(raw.startswith(KEY_PREFIX))
        self.assertGreater(len(raw), 40)
        self.assertEqual(key.prefix, raw[:10])
        self.assertEqual(key.key_hash, hash_key(raw))
        stored = ApiKey.objects.values().get(pk=key.pk)
        self.assertNotIn(raw, ' '.join(str(v) for v in stored.values()))

    def test_every_key_is_different(self):
        user = make_user()
        self.assertNotEqual(ApiKey.issue(user, 'a')[1], ApiKey.issue(user, 'b')[1])


class ApiKeyPageTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)

    def test_pages_need_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse('accounts:api-keys')).status_code, 302)
        self.assertEqual(self.client.post(reverse('accounts:api-key-create'), {'name': 'x'}).status_code, 302)

    def test_a_new_key_is_shown_once_and_never_again(self):
        response = self.client.post(reverse('accounts:api-key-create'), {'name': 'Zapier'})
        raw = response.context['new_key']
        self.assertContains(response, raw)
        self.assertEqual(response['Cache-Control'], 'no-store')
        again = self.client.get(reverse('accounts:api-keys'))
        self.assertNotContains(again, raw)
        self.assertContains(again, raw[:10])
        self.assertContains(again, 'Zapier')

    def test_a_name_is_required(self):
        response = self.client.post(reverse('accounts:api-key-create'), {'name': '   '})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(ApiKey.objects.exists())

    def test_key_names_are_escaped(self):
        ApiKey.issue(self.user, '<script>alert(1)</script>')
        response = self.client.get(reverse('accounts:api-keys'))
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.assertContains(response, '&lt;script&gt;')

    @override_settings(MAX_API_KEYS_PER_USER=2)
    def test_the_number_of_active_keys_is_limited(self):
        for name in ('a', 'b', 'c'):
            self.client.post(reverse('accounts:api-key-create'), {'name': name})
        self.assertEqual(ApiKey.objects.count(), 2)
        key = ApiKey.objects.first()
        self.client.post(reverse('accounts:api-key-revoke', args=[key.pk]))
        self.client.post(reverse('accounts:api-key-create'), {'name': 'd'})
        self.assertEqual(ApiKey.objects.count(), 3)

    def test_revoking_a_key(self):
        key, _ = ApiKey.issue(self.user, 'old')
        response = self.client.post(reverse('accounts:api-key-revoke', args=[key.pk]))
        self.assertRedirects(response, reverse('accounts:api-keys'))
        key.refresh_from_db()
        self.assertFalse(key.is_active)

    def test_revoking_needs_a_post(self):
        key, _ = ApiKey.issue(self.user, 'old')
        self.assertEqual(self.client.get(reverse('accounts:api-key-revoke', args=[key.pk])).status_code, 405)
        key.refresh_from_db()
        self.assertTrue(key.is_active)

    def test_nobody_can_revoke_another_users_key(self):
        other_key, _ = ApiKey.issue(make_user('other'), 'theirs')
        self.assertEqual(self.client.post(reverse('accounts:api-key-revoke', args=[other_key.pk])).status_code, 404)
        other_key.refresh_from_db()
        self.assertTrue(other_key.is_active)

    def test_nobody_sees_another_users_keys(self):
        ApiKey.issue(make_user('other'), 'THEIRS-KEY')
        self.assertNotContains(self.client.get(reverse('accounts:api-keys')), 'THEIRS-KEY')
