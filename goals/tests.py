from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User


class GoalsViewTests(TestCase):
    def test_goals_requires_login(self):
        resp = self.client.get(reverse('goals'))
        self.assertEqual(resp.status_code, 302)  # redirect to login

    def test_create_goal_logged_in(self):
        u = User.objects.create_user('tester', 't@example.com', 'pass')
        self.client.login(username='tester', password='pass')
        resp = self.client.get(reverse('create-goal'))
        self.assertEqual(resp.status_code, 200)
