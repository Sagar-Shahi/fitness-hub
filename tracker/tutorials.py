import hashlib
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@login_required
@require_GET
def exercise_library_tutorials(request):
    """Find embeddable public exercise videos for a catalogue exercise."""
    name = " ".join(request.GET.get("name", "").split())[:80]
    if not name:
        return JsonResponse({"error": "Choose an exercise first."}, status=400)

    api_key = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if not api_key:
        return JsonResponse({"error": "Tutorial search is being set up. Please try again shortly."}, status=503)

    query = f"{name} exercise proper form tutorial"
    cache_key = "fithub:youtube:" + hashlib.sha256(query.lower().encode("utf-8")).hexdigest()
    cached = cache.get(cache_key)
    if cached is not None:
        return JsonResponse({"videos": cached})

    rate_key = f"fithub:youtube:rate:{request.user.pk}"
    count = cache.get(rate_key, 0)
    if count >= 8:
        return JsonResponse({"error": "Please wait a minute before searching for more tutorials."}, status=429)
    cache.set(rate_key, count + 1, 60)

    params = urlencode({
        "part": "snippet",
        "type": "video",
        "maxResults": 1,
        "safeSearch": "strict",
        "q": query,
        "videoEmbeddable": "true",
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
        return JsonResponse({"error": "Could not load tutorials right now. Please try again."}, status=502)
    except (URLError, TimeoutError, ValueError):
        return JsonResponse({"error": "Could not connect to YouTube. Please try again."}, status=502)

    videos = []
    for item in payload.get("items", []):
        video_id = item.get("id", {}).get("videoId", "")
        snippet = item.get("snippet", {})
        if not video_id or len(video_id) != 11:
            continue
        thumbnails = snippet.get("thumbnails", {})
        thumbnail = (thumbnails.get("medium") or thumbnails.get("default") or {}).get("url", "")
        videos.append({
            "id": video_id,
            "title": snippet.get("title", "Exercise tutorial"),
            "channel": snippet.get("channelTitle", ""),
            "thumbnail": thumbnail,
        })
    cache.set(cache_key, videos, 60 * 60 * 24)
    return JsonResponse({"videos": videos})
