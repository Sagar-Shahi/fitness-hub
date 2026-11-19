import hashlib
import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.cache import caches
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_GET

from .models import Exercise


def _increment_window(cache, key, timeout):
    """Atomically enough for the shared cache: initialise, then increment a short-lived counter."""
    cache.add(key, 0, timeout=timeout)
    try:
        return cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=timeout)
        return 1


def search_youtube_videos(request, query, *, cache_prefix, max_results, cache_timeout, missing_key_message):
    """Shared, quota-limited YouTube search for music and exercise tutorials."""
    research_cache = caches["research"]
    normalized_query = " ".join(query.split()).casefold()
    cache_key = cache_prefix + hashlib.sha256(normalized_query.encode("utf-8")).hexdigest()

    # Cached public results remain available even when the API key is absent or the quota is spent.
    cached = research_cache.get(cache_key)
    if cached is not None:
        return JsonResponse({"videos": cached})

    api_key = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if not api_key:
        return JsonResponse({"error": missing_key_message}, status=503)

    # One shared per-user limit covers every FitHub YouTube search surface.
    rate_key = f"fithub:youtube:rate:{request.user.pk}"
    if _increment_window(research_cache, rate_key, 60) > 8:
        return JsonResponse({"error": "Please wait a minute before searching again."}, status=429)

    # Search.list costs 100 quota units. Keep all live searches under the configured daily budget.
    daily_key = f"fithub:youtube:daily:{timezone.localdate().isoformat()}"
    daily_count = _increment_window(research_cache, daily_key, 60 * 60 * 30)
    if daily_count > max(0, settings.YOUTUBE_DAILY_SEARCH_LIMIT):
        return JsonResponse({
            "error": "FitHub has reached today's live-search limit. Cached results are still available; please try again tomorrow."
        }, status=429)

    params = urlencode({
        "part": "snippet",
        "type": "video",
        "maxResults": max(1, min(int(max_results), 8)),
        "safeSearch": "strict",
        "videoEmbeddable": "true",
        "q": query,
        "key": api_key,
    })
    req = Request(
        "https://www.googleapis.com/youtube/v3/search?" + params,
        headers={"Accept": "application/json", "User-Agent": "FitHub/1.0"},
    )
    try:
        with urlopen(req, timeout=8) as response:  # nosec
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 403:
            return JsonResponse({"error": "YouTube search is temporarily unavailable. Please try again later."}, status=503)
        return JsonResponse({"error": "Could not search YouTube right now. Please try again."}, status=502)
    except (URLError, TimeoutError, ValueError, UnicodeDecodeError):
        return JsonResponse({"error": "Could not connect to YouTube. Please try again."}, status=502)

    items = payload.get("items") or []
    if not isinstance(items, list):
        items = []
    videos = []
    for item in items:
        if not isinstance(item, dict):
            continue
        video_id = item.get("id", {}).get("videoId", "") if isinstance(item.get("id"), dict) else ""
        snippet = item.get("snippet") if isinstance(item.get("snippet"), dict) else {}
        if not isinstance(video_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
            continue
        thumbnails = snippet.get("thumbnails") if isinstance(snippet.get("thumbnails"), dict) else {}
        thumbnail = (thumbnails.get("medium") or thumbnails.get("default") or {}).get("url", "")
        if not isinstance(thumbnail, str) or not thumbnail.startswith("https://i.ytimg.com/"):
            thumbnail = ""
        title = snippet.get("title")
        channel = snippet.get("channelTitle")
        videos.append({
            "id": video_id,
            "title": title if isinstance(title, str) and title else "YouTube video",
            "channel": channel if isinstance(channel, str) else "",
            "thumbnail": thumbnail,
        })

    # Cache empty results too, so repeated searches do not burn quota.
    research_cache.set(cache_key, videos, cache_timeout)
    return JsonResponse({"videos": videos})


@login_required
@require_GET
def exercise_library_tutorials(request):
    """Find embeddable public exercise videos, reusing shared results before using quota."""
    name = " ".join(request.GET.get("name", "").split())[:80]
    if not name:
        return JsonResponse({"error": "Choose an exercise first."}, status=400)
    query = f"{name} exercise proper form tutorial"
    return search_youtube_videos(
        request,
        query,
        cache_prefix="fithub:youtube:exercise:",
        max_results=1,
        cache_timeout=60 * 60 * 24,
        missing_key_message="Tutorial search is being set up. Please try again shortly.",
    )


@login_required
@require_GET
def exercise_workout_tutorials(request, exercise_pk):
    """Use the same protected, quota-limited tutorial search from a logged workout."""
    exercise = get_object_or_404(
        Exercise.objects.select_related("workout").filter(workout__owner=request.user),
        pk=exercise_pk,
    )
    query = f"{exercise.name} exercise proper form tutorial"
    return search_youtube_videos(
        request,
        query,
        cache_prefix="fithub:youtube:exercise:",
        max_results=1,
        cache_timeout=60 * 60 * 24,
        missing_key_message="Tutorial search is being set up. Please try again shortly.",
    )
