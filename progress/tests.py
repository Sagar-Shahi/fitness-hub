from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User


class ProgressViewTests(TestCase):
    def test_progress_requires_login(self):
        resp = self.client.get(reverse('progress'))
        self.assertEqual(resp.status_code, 302)

    def test_progress_logged_in(self):
        u = User.objects.create_user('puser', 'p@example.com', 'pass')
        self.client.login(username='puser', password='pass')
        resp = self.client.get(reverse('progress'))
        self.assertEqual(resp.status_code, 200)
