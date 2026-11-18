import json
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from .testutils import make_user


class ExerciseLibraryTutorialTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = make_user("tutorial-viewer")
        self.url = reverse("tracker:exercise-library-tutorials")

    def test_tutorial_search_requires_login(self):
        response = self.client.get(self.url, {"name": "Bench Press"})
        self.assertEqual(response.status_code, 302)

    @patch.dict("os.environ", {"YOUTUBE_API_KEY": "private-test-key"})
    @patch("tracker.tutorials.urlopen")
    def test_search_returns_embeddable_video_metadata_without_exposing_key(self, mocked_urlopen):
        response_mock = mocked_urlopen.return_value.__enter__.return_value
        response_mock.read.return_value = json.dumps({
            "items": [{
                "id": {"videoId": "abcdefghijk"},
                "snippet": {
                    "title": "Bench Press Form Guide",
                    "channelTitle": "Training Channel",
                    "thumbnails": {"medium": {"url": "https://i.ytimg.com/vi/abcdefghijk/mqdefault.jpg"}},
                },
            }],
        }).encode()
        self.client.force_login(self.user)

        response = self.client.get(self.url, {"name": "Bench Press"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["videos"][0]["id"], "abcdefghijk")
        self.assertEqual(response.json()["videos"][0]["title"], "Bench Press Form Guide")
        self.assertNotContains(response, "private-test-key")
        self.assertIn("videoEmbeddable=true", mocked_urlopen.call_args.args[0].full_url)

    def test_empty_exercise_name_is_rejected(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, {"name": " "})
        self.assertEqual(response.status_code, 400)
