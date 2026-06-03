from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User


class DietViewTests(TestCase):
    def test_diet_requires_login(self):
        resp = self.client.get(reverse('diet'))
        self.assertEqual(resp.status_code, 302)

    def test_create_record_view_logged_in(self):
        u = User.objects.create_user('dietuser', 'd@example.com', 'pass')
        self.client.login(username='dietuser', password='pass')
        resp = self.client.get(reverse('create-record'))
        self.assertEqual(resp.status_code, 200)
