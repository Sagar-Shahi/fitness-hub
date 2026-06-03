from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

class UserLogoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='logoutuser',
            email='logout@example.com',
            password='StrongPass123'
        )
        self.client = Client()

    def test_logout_redirects_to_home(self):
        self.client.login(username='logoutuser', password='StrongPass123')
        response = self.client.post(reverse('logout'), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain[-1][0], reverse('home'))
        self.assertEqual(response.redirect_chain[-1][1], 302)
        self.assertContains(response, 'Fitness Hub')
        self.assertNotContains(response, 'Logout')
