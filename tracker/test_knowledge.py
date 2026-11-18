from django.test import TestCase
from django.urls import reverse

from .testutils import make_user


class LearnPageTests(TestCase):
    def setUp(self):
        self.user = make_user("learn-reader")
        self.client.force_login(self.user)
        self.url = reverse("tracker:learn")

    def test_learn_page_shows_curated_lessons_and_sources(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Train with understanding.")
        self.assertContains(response, "The weekly activity baseline")
        self.assertContains(response, "Protein and training: what matters")
        self.assertContains(response, "Strength vs muscle growth: train with a purpose")
        self.assertContains(response, "Hydration basics for training")
        self.assertContains(response, "Your major muscle groups, explained")
        self.assertContains(response, "How muscles work: the simple science")
        self.assertContains(response, "openstax.org")
        self.assertContains(response, "ACSM — 2026 resistance training position stand")
        self.assertContains(response, "Sources and further reading")
        self.assertContains(response, "pmc.ncbi.nlm.nih.gov")

    def test_search_filters_lessons(self):
        response = self.client.get(self.url, {"q": "protein"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Protein and training: what matters")
        self.assertNotContains(response, "The weekly activity baseline")

    def test_category_filter(self):
        response = self.client.get(self.url, {"category": "Recovery"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Recovery is part of the programme")
        self.assertNotContains(response, "The weekly activity baseline")

    def test_unknown_category_does_not_hide_everything(self):
        response = self.client.get(self.url, {"category": "unknown"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The weekly activity baseline")

    def test_page_requires_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith(reverse("accounts:login")))
