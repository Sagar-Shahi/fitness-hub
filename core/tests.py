import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from unittest import SkipTest, mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from . import throttle
from .views import error_500


class ClientIpTests(TestCase):
    def _request(self, **meta):
        return RequestFactory().get('/', **meta)

    def test_without_a_trusted_proxy_a_forged_forwarded_header_is_ignored(self):
        request = self._request(REMOTE_ADDR='203.0.113.5', HTTP_X_FORWARDED_FOR='1.2.3.4')
        self.assertEqual(throttle.client_ip(request), '203.0.113.5')

    @override_settings(TRUSTED_PROXY_COUNT=1)
    def test_with_one_proxy_the_last_forwarded_address_is_used(self):
        request = self._request(REMOTE_ADDR='10.0.0.1', HTTP_X_FORWARDED_FOR='6.6.6.6, 198.51.100.7')
        self.assertEqual(throttle.client_ip(request), '198.51.100.7')  # a visitor-supplied 6.6.6.6 is ignored

    @override_settings(TRUSTED_PROXY_COUNT=2)
    def test_with_two_proxies_the_second_from_the_right_is_used(self):
        request = self._request(REMOTE_ADDR='10.0.0.1', HTTP_X_FORWARDED_FOR='9.9.9.9, 198.51.100.7, 172.16.0.3')
        self.assertEqual(throttle.client_ip(request), '198.51.100.7')

    @override_settings(TRUSTED_PROXY_COUNT=1)
    def test_a_missing_or_invalid_forwarded_header_falls_back_to_the_connection_address(self):
        self.assertEqual(throttle.client_ip(self._request(REMOTE_ADDR='10.0.0.1')), '10.0.0.1')
        request = self._request(REMOTE_ADDR='10.0.0.1', HTTP_X_FORWARDED_FOR='not-an-ip')
        self.assertEqual(throttle.client_ip(request), '10.0.0.1')

    @override_settings(TRUSTED_PROXY_COUNT=3)
    def test_fewer_forwarded_entries_than_proxies_falls_back(self):
        request = self._request(REMOTE_ADDR='10.0.0.1', HTTP_X_FORWARDED_FOR='198.51.100.7')
        self.assertEqual(throttle.client_ip(request), '10.0.0.1')


class ThrottleTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_counting_and_resetting(self):
        key = throttle.make_key('t', 'a')
        self.assertEqual([throttle.hit(key, 60) for _ in range(3)], [1, 2, 3])
        self.assertEqual(throttle.count(key), 3)
        throttle.reset(key)
        self.assertEqual(throttle.count(key), 0)

    def test_exceeded_only_after_the_limit(self):
        key = throttle.make_key('t', 'b')
        self.assertEqual([throttle.exceeded(key, 2, 60) for _ in range(4)], [False, False, True, True])

    def test_keys_have_a_fixed_length_and_differ_per_input(self):
        long_key = throttle.make_key('login', '1.2.3.4', 'x' * 5000)
        self.assertLess(len(long_key), 60)
        self.assertNotEqual(throttle.make_key('a', '1'), throttle.make_key('a', '2'))


class SecurityHeaderTests(TestCase):
    def test_public_pages_send_a_strict_content_security_policy(self):
        response = self.client.get('/')
        csp = response['Content-Security-Policy']
        self.assertIn("script-src 'self'", csp)
        self.assertIn("style-src 'self';", csp)
        self.assertNotIn('unsafe-inline', csp)
        self.assertNotIn('unsafe-eval', csp)
        self.assertIn("frame-ancestors 'none'", csp)
        self.assertIn("object-src 'none'", csp)

    def test_other_security_headers(self):
        response = self.client.get('/')
        self.assertEqual(response['X-Frame-Options'], 'DENY')
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(response['Referrer-Policy'], 'same-origin')
        self.assertEqual(response['Cache-Control'], 'no-store')
        self.assertIn('camera=()', response['Permissions-Policy'])

    def test_only_the_admin_is_allowed_inline_styles(self):
        response = self.client.get(reverse('admin:login'))
        self.assertIn("style-src 'self' 'unsafe-inline'", response['Content-Security-Policy'])
        self.assertIn("script-src 'self';", response['Content-Security-Policy'])

    def test_templates_contain_no_inline_scripts_styles_or_event_handlers(self):
        problems = []
        for path in Path(settings.BASE_DIR, 'templates').rglob('*.html'):
            text = path.read_text()
            if re.search(r'\sstyle\s*=|\son[a-z]+\s*=|<style|<script(?![^>]*\ssrc=)', text, re.IGNORECASE):
                problems.append(path.name)
        self.assertEqual(problems, [], 'These templates would be blocked by the Content-Security-Policy')


class HealthAndErrorTests(TestCase):
    def test_health_check(self):
        response = self.client.get(reverse('health'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})

    def test_health_check_reports_a_database_problem_without_details(self):
        with mock.patch('core.views.connection.ensure_connection', side_effect=Exception('secret db host')):
            with self.assertLogs('core.views', level='ERROR'):
                response = self.client.get(reverse('health'))
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('secret', response.content.decode())

    def test_unknown_pages_show_the_friendly_404(self):
        response = self.client.get('/no-such-page/')
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, 'could not find that page', status_code=404)

    def test_the_500_page_is_generic(self):
        response = error_500(RequestFactory().get('/'))
        self.assertEqual(response.status_code, 500)
        body = response.content.decode()
        self.assertIn('Something went wrong', body)
        self.assertNotIn('Traceback', body)

    def test_home_page_only_accepts_safe_methods(self):
        self.assertEqual(self.client.post('/').status_code, 405)


class AdminLoginThrottleTests(TestCase):
    def setUp(self):
        cache.clear()
        get_user_model().objects.create_superuser('boss', 'boss@example.com', 'Sup3r-secret-pass-1')
        self.url = reverse('admin:login')

    def _post(self, password, **extra):
        return self.client.post(self.url, {'username': 'boss', 'password': password}, **extra)

    @override_settings(LOGIN_MAX_FAILURES=3)
    def test_the_admin_login_locks_out_after_too_many_failures(self):
        for _ in range(3):
            self.assertEqual(self._post('wrong-password').status_code, 200)
        response = self._post('Sup3r-secret-pass-1')
        self.assertEqual(response.status_code, 429)
        self.assertIn('Retry-After', response)
        self.assertNotIn('_auth_user_id', self.client.session)

    @override_settings(LOGIN_MAX_FAILURES=3)
    def test_other_addresses_are_not_locked_out(self):
        for _ in range(3):
            self._post('wrong-password', REMOTE_ADDR='203.0.113.1')
        response = self._post('Sup3r-secret-pass-1', REMOTE_ADDR='203.0.113.2')
        self.assertEqual(response.status_code, 302)

    def test_a_correct_login_works_and_resets_the_counter(self):
        self._post('wrong-password')
        self.assertEqual(self._post('Sup3r-secret-pass-1').status_code, 302)
        self.assertEqual(throttle.count(throttle.make_key('admin-login-fail', '127.0.0.1')), 0)

    def test_the_admin_is_not_at_the_default_address(self):
        self.assertEqual(self.client.get('/admin/login/').status_code, 404)


class ProductionSettingsTests(TestCase):
    """Starts a fresh Python process, because settings are read once when it starts."""

    GOOD_KEY = 'k8#vQ2mZp!xR7tLw9sYb4nHc6Ed1JfGuA3oXiKq5VzMrTyWBPe0'

    def _manage(self, *args, **env):
        base = {k: v for k, v in os.environ.items() if not k.startswith(('DJANGO_', 'DATABASE_'))}
        base.update({'DJANGO_SECRET_KEY': '', 'DJANGO_DEBUG': ''})
        base.update(env)
        return subprocess.run(
            [sys.executable, 'manage.py', *args], cwd=settings.BASE_DIR, env=base,
            capture_output=True, text=True, timeout=120,
        )

    def test_without_any_settings_the_site_refuses_to_start_instead_of_running_in_debug_mode(self):
        result = self._manage('check')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('DJANGO_SECRET_KEY', result.stderr)

    def test_a_secret_key_without_allowed_hosts_is_refused(self):
        result = self._manage('check', DJANGO_SECRET_KEY=self.GOOD_KEY)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('DJANGO_ALLOWED_HOSTS', result.stderr)

    def test_production_settings_pass_djangos_deployment_check(self):
        result = self._manage(
            'check', '--deploy', '--fail-level', 'WARNING',
            DJANGO_SECRET_KEY=self.GOOD_KEY, DJANGO_ALLOWED_HOSTS='fit.example.com',
            DJANGO_HSTS_SECONDS='31536000', DJANGO_HSTS_INCLUDE_SUBDOMAINS='True', DJANGO_HSTS_PRELOAD='True',
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_debug_mode_has_to_be_switched_on_explicitly(self):
        result = self._manage('check', DJANGO_DEBUG='True')
        self.assertEqual(result.returncode, 0, result.stderr)


class RepositoryHygieneTests(TestCase):
    """Cheap checks that run on every push, so a secret or a local file is never committed by accident."""

    SECRET_PATTERNS = {
        'Stripe key': r'sk_(?:live|test)_[A-Za-z0-9]{16,}',
        'AWS access key': r'AKIA[0-9A-Z]{16}',
        'private key': r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----',
        'GitHub token': r'(?:ghp|gho|ghs|ghu)_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}',
        'Slack token': r'xox[baprs]-[A-Za-z0-9-]{10,}',
        'FitHub API key': r'\bfh_[A-Za-z0-9_-]{40,}',
    }

    def _files(self):
        if shutil.which('git') is None or not (Path(settings.BASE_DIR) / '.git').exists():
            raise SkipTest('Not a git checkout')
        listing = subprocess.run(
            ['git', 'ls-files', '--cached', '--others', '--exclude-standard'],
            cwd=settings.BASE_DIR, capture_output=True, text=True, check=True,
        ).stdout.splitlines()
        return [Path(settings.BASE_DIR, name) for name in listing]

    def test_no_secrets_in_the_project_files(self):
        findings = []
        for path in self._files():
            if not path.is_file() or path.suffix in {'.png', '.jpg', '.gz', '.ico'}:
                continue
            try:
                text = path.read_text()
            except UnicodeDecodeError:
                continue
            for label, pattern in self.SECRET_PATTERNS.items():
                if re.search(pattern, text):
                    findings.append(f'{label} in {path.relative_to(settings.BASE_DIR)}')
        self.assertEqual(findings, [])

    def test_local_files_are_never_committed(self):
        names = {str(p.relative_to(settings.BASE_DIR)) for p in self._files()}
        self.assertNotIn('.env', names)
        self.assertNotIn('db.sqlite3', names)
        self.assertFalse([n for n in names if n.startswith('staticfiles/')])

    def test_the_example_env_file_contains_no_real_values(self):
        text = (Path(settings.BASE_DIR) / '.env.example').read_text()
        active = [line for line in text.splitlines() if line.strip() and not line.lstrip().startswith('#')]
        self.assertEqual(active, ['DJANGO_DEBUG=True'])
