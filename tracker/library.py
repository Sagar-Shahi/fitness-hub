"""Public-domain exercise catalogue view for FitHub."""
import json
from urllib.error import URLError
from urllib.request import Request, urlopen
from urllib.parse import quote

from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import render
from django.urls import reverse

from .models import Workout

CATALOG_URL = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json"
CATALOG_CACHE_KEY = "fithub:exercise-library:v1"


def _catalog():
    cached = cache.get(CATALOG_CACHE_KEY)
    if cached is not None:
        return cached, None
    request = Request(CATALOG_URL, headers={"Accept": "application/json", "User-Agent": "FitHub/1.0"})
    try:
        with urlopen(request, timeout=12) as response:  # nosec
            payload = json.loads(response.read().decode("utf-8"))
        if not isinstance(payload, list):
            raise ValueError("Unexpected exercise catalogue format")
        cache.set(CATALOG_CACHE_KEY, payload, 60 * 60 * 24)
        return payload, None
    except (URLError, TimeoutError, ValueError, UnicodeDecodeError):
        return [], "The exercise catalogue is temporarily unavailable. Please try again shortly."


@login_required
def exercise_library(request):
    exercises, error = _catalog()
    query = request.GET.get("q", "").strip()[:80]
    muscle = request.GET.get("muscle", "").strip().lower()[:40]
    equipment = request.GET.get("equipment", "").strip().lower()[:40]
    level = request.GET.get("level", "").strip().lower()[:20]
    category = request.GET.get("category", "").strip().lower()[:30]
    workout_id = request.GET.get("workout", "").strip()
    selected_workout = None
    if workout_id.isdigit():
        selected_workout = Workout.objects.filter(owner=request.user, pk=int(workout_id)).first()

    muscles = sorted({m for item in exercises for m in item.get("primaryMuscles", []) if isinstance(m, str)})
    equipment_types = sorted({item.get("equipment") for item in exercises if item.get("equipment")})
    levels = sorted({str(item.get("level")) for item in exercises if item.get("level")})
    categories = sorted({str(item.get("category")) for item in exercises if item.get("category")})
    filtered = []
    for item in exercises:
        name = str(item.get("name", ""))
        primary = item.get("primaryMuscles") or []
        item_equipment = str(item.get("equipment") or "")
        secondary = item.get("secondaryMuscles") or []
        item_level = str(item.get("level") or "").lower()
        item_category = str(item.get("category") or "").lower()
        haystack = " ".join([name, item_equipment, item_category, " ".join(primary), " ".join(secondary)]).lower()
        if query and query.lower() not in haystack:
            continue
        if muscle and muscle not in [str(m).lower() for m in primary]:
            continue
        if equipment and item_equipment.lower() != equipment:
            continue
        if level and item_level != level:
            continue
        if category and item_category != category:
            continue
        image_paths = item.get("images") or []
        image_path = image_paths[0] if image_paths and isinstance(image_paths[0], str) else ""
        exercise_id = str(item.get("id") or "")
        if image_path and exercise_id and image_path.startswith(exercise_id + "/") and ".." not in image_path.split("/"):
            item["image_url"] = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/" + quote(image_path, safe="/")
        else:
            item["image_url"] = ""
        filtered.append(item)

    raw_page = request.GET.get("page", "1")
    page = int(raw_page) if raw_page.isdigit() and len(raw_page) <= 6 else 1
    page_size = 24
    page_count = max(1, (len(filtered) + page_size - 1) // page_size)
    page = min(max(1, page), page_count)
    start = (page - 1) * page_size
    page_items = filtered[start:start + page_size]
    return render(request, "tracker/exercise_library.html", {
        "exercises": page_items,
        "query": query,
        "muscle": muscle,
        "equipment": equipment,
        "level": level,
        "category": category,
        "muscles": muscles,
        "equipment_types": equipment_types,
        "levels": levels,
        "categories": categories,
        "selected_workout": selected_workout,
        "workouts": Workout.objects.filter(owner=request.user).order_by("-date", "-id")[:100],
        "result_count": len(filtered),
        "page": page,
        "page_count": page_count,
        "previous_page": page - 1 if page > 1 else None,
        "next_page": page + 1 if page < page_count else None,
        "error": error,
        "catalogue_source": "Free Exercise DB (Unlicense / public domain)",
    })
