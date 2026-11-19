import json
from unittest.mock import patch

from django.core.cache import cache, caches
from django.test import TestCase, override_settings
from django.urls import reverse

from .testutils import make_user


class ExerciseLibraryTutorialTests(TestCase):
    def setUp(self):
        cache.clear()
        caches["research"].clear()
        self.user = make_user("tutorial-viewer")
        self.url = reverse("tracker:exercise-library-tutorials")

    def _youtube_response(self, mocked_urlopen):
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

    def test_tutorial_search_requires_login(self):
        response = self.client.get(self.url, {"name": "Bench Press"})
        self.assertEqual(response.status_code, 302)

    @patch.dict("os.environ", {"YOUTUBE_API_KEY": "private-test-key"})
    @patch("tracker.tutorials.urlopen")
    def test_search_returns_embeddable_video_metadata_without_exposing_key(self, mocked_urlopen):
        self._youtube_response(mocked_urlopen)
        self.client.force_login(self.user)

        response = self.client.get(self.url, {"name": "Bench Press"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["videos"][0]["id"], "abcdefghijk")
        self.assertEqual(response.json()["videos"][0]["title"], "Bench Press Form Guide")
        self.assertNotContains(response, "private-test-key")
        self.assertIn("videoEmbeddable=true", mocked_urlopen.call_args.args[0].full_url)

    @patch.dict("os.environ", {"YOUTUBE_API_KEY": "private-test-key"})
    @patch("tracker.tutorials.urlopen")
    def test_cached_result_is_shared_and_served_without_api_key(self, mocked_urlopen):
        self._youtube_response(mocked_urlopen)
        self.client.force_login(self.user)
        first = self.client.get(self.url, {"name": "Bench Press"})
        self.assertEqual(first.status_code, 200)

        other_user = make_user("tutorial-viewer-two")
        self.client.force_login(other_user)
        with patch.dict("os.environ", {"YOUTUBE_API_KEY": ""}):
            second = self.client.get(self.url, {"name": " bench   press "})

        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.json(), first.json())
        mocked_urlopen.assert_called_once()

    @override_settings(YOUTUBE_DAILY_SEARCH_LIMIT=1)
    @patch.dict("os.environ", {"YOUTUBE_API_KEY": "private-test-key"})
    @patch("tracker.tutorials.urlopen")
    def test_daily_live_search_budget_stops_new_api_calls(self, mocked_urlopen):
        self._youtube_response(mocked_urlopen)
        self.client.force_login(self.user)
        first = self.client.get(self.url, {"name": "Bench Press"})
        second = self.client.get(self.url, {"name": "Incline Press"})

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 429)
        mocked_urlopen.assert_called_once()

    def test_empty_exercise_name_is_rejected(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, {"name": " "})
        self.assertEqual(response.status_code, 400)


class WorkoutExerciseTutorialTests(TestCase):
    def setUp(self):
        cache.clear()
        caches["research"].clear()
        self.user = make_user("workout-tutorial-owner")
        self.client.force_login(self.user)

    @patch.dict("os.environ", {"YOUTUBE_API_KEY": "private-test-key"})
    @patch("tracker.tutorials.urlopen")
    def test_workout_tutorial_uses_shared_quota_limited_search(self, mocked_urlopen):
        response_mock = mocked_urlopen.return_value.__enter__.return_value
        response_mock.read.return_value = json.dumps({
            "items": [{
                "id": {"videoId": "abcdefghijk"},
                "snippet": {"title": "Bench Press Form", "channelTitle": "Training"},
            }],
        }).encode()
        from .testutils import make_workout
        workout = make_workout(self.user, exercises=(("Bench Press", 3, 8, "60"),))
        exercise = workout.exercises.first()
        response = self.client.get(reverse("tracker:exercise-tutorials", args=[exercise.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["videos"][0]["id"], "abcdefghijk")
        self.assertIn("videoEmbeddable=true", mocked_urlopen.call_args.args[0].full_url)

    def test_workout_tutorial_cannot_read_another_users_exercise(self):
        from .testutils import make_workout
        other = make_user("workout-tutorial-other")
        workout = make_workout(other, exercises=(("Private lift", 2, 8, "20"),))
        exercise = workout.exercises.first()
        response = self.client.get(reverse("tracker:exercise-tutorials", args=[exercise.pk]))
        self.assertEqual(response.status_code, 404)
