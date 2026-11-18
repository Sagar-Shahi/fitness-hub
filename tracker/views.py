import csv
import hashlib
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.core.cache import cache
from django.db import transaction
from django.db.models import Count
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from . import analytics
from .forms import ExerciseForm, ExerciseSetAddForm, ExerciseSetForm, MealForm, ProfileForm, WeightForm, WorkoutForm
from .models import BodyMetric, Exercise, ExerciseSet, Meal, Workout, profile_for
from shop.models import OrderItem

PAGE_SIZE = 15
PERIODS = (7, 30, 90)


def _days(request, default=30):
    try:
        value = int(request.GET.get('days', default))
    except (TypeError, ValueError):
        return default
    return value if value in PERIODS else default


def _own_workout(request, pk):
    return get_object_or_404(Workout.objects.filter(owner=request.user).prefetch_related('exercises__set_entries'), pk=pk)


def _attach_set_forms(workout, bound_form=None):
    for exercise in workout.exercises.all():
        last_entry = exercise.set_entries.order_by('-set_number').first()
        defaults = {'reps': last_entry.reps, 'weight_kg': last_entry.weight_kg} if last_entry else {
            'reps': exercise.reps, 'weight_kg': exercise.weight_kg,
        }
        exercise.add_set_form = ExerciseSetAddForm(prefix=f'add-set-{exercise.pk}', initial=defaults)
        for entry in exercise.set_entries.all():
            prefix = f'set-{entry.pk}'
            entry.edit_form = (bound_form if bound_form is not None and bound_form.instance.pk == entry.pk
                               else ExerciseSetForm(instance=entry, prefix=prefix))
    return workout


def _csv_safe(value):
    text = str(value)
    return "'" + text if text[:1] in ('=', '+', '-', '@', '\t', '\r') else text


@login_required
def dashboard(request):
    profile = profile_for(request.user)
    days = _days(request)
    data = analytics.dashboard(request.user, profile)
    data['week_percent'] = analytics.percent(data['week_done'], data['week_target'])
    data['calorie_percent'] = analytics.percent(data['today']['calories'], data['calorie_target'])
    recent = (Workout.objects.filter(owner=request.user).prefetch_related('exercises__set_entries')[:5])
    return render(request, 'tracker/dashboard.html', {
        'days': days, 'periods': PERIODS, 'd': data,
        'workout_chart': analytics.bar_chart(analytics.workouts_per_day(request.user, days), 'workouts'),
        'calorie_chart': analytics.bar_chart(analytics.calories_per_day(request.user, 14), 'kcal'),
        'weight_chart': analytics.line_chart(analytics.weight_points(request.user, days), target=profile.target_weight_kg),
        'recent': recent,
        'has_data': Workout.objects.filter(owner=request.user).exists() or Meal.objects.filter(owner=request.user).exists()
                    or BodyMetric.objects.filter(owner=request.user).exists(),
    })



@login_required
def share_progress(request):
    """Prepare a privacy-conscious, non-public progress summary for the signed-in user."""
    end = timezone.localdate()
    start = end - timedelta(days=29)
    workouts = Workout.objects.filter(owner=request.user, date__gte=start, date__lte=end).count()
    completed_sets = ExerciseSet.objects.filter(
        exercise__workout__owner=request.user,
        exercise__workout__date__gte=start,
        exercise__workout__date__lte=end,
        is_completed=True,
    ).count()
    streak_days = analytics.streak(request.user)
    share_text = (
        f"I logged {workouts} workouts and completed {completed_sets} sets "
        f"in the last 30 days with FitHub. Consistency is built rep by rep."
    )
    return render(request, 'tracker/share_progress.html', {
        'workouts': workouts,
        'completed_sets': completed_sets,
        'streak_days': streak_days,
        'share_text': share_text,
        'period_start': start,
        'period_end': end,
    })


@login_required
def goals(request):
    profile = profile_for(request.user)
    form = ProfileForm(request.POST or None, instance=profile)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Goals saved.')
        return redirect('tracker:dashboard')
    items = (OrderItem.objects.filter(order__owner=request.user).select_related('plan', 'order')
             .order_by('-order__created_at'))
    seen, my_plans = set(), []
    for item in items:
        if item.plan_id not in seen:
            seen.add(item.plan_id)
            my_plans.append(item)
    return render(request, 'tracker/goals.html', {'form': form, 'my_plans': my_plans})


@login_required
def workout_list(request):
    qs = Workout.objects.filter(owner=request.user).annotate(n_exercises=Count('exercises')).order_by('-date', '-id')
    page = Paginator(qs, PAGE_SIZE).get_page(request.GET.get('page'))
    return render(request, 'tracker/workout_list.html', {'page': page, 'total': qs.count()})


@login_required
def workout_create(request):
    form = WorkoutForm(request.POST or None, owner=request.user)
    if request.method == 'POST' and form.is_valid():
        workout = form.save(commit=False)
        workout.owner = request.user
        workout.save()
        messages.success(request, 'Workout saved. Now add the exercises.')
        return redirect('tracker:workout-detail', pk=workout.pk)
    return render(request, 'tracker/workout_form.html', {'form': form, 'title': 'Log a workout'})



@login_required
@require_GET
def exercise_tutorials(request, exercise_pk):
    """Search public YouTube exercise tutorials without exposing FitHub's API key."""
    exercise = get_object_or_404(
        Exercise.objects.select_related('workout').filter(workout__owner=request.user),
        pk=exercise_pk,
    )
    api_key = os.environ.get('YOUTUBE_API_KEY', '').strip()
    if not api_key:
        return JsonResponse({'error': 'Tutorial search is being set up. Please try again shortly.'}, status=503)

    # Cache successful searches for a day to conserve the YouTube API's daily quota.
    query = f"{exercise.name} exercise proper form tutorial"
    cache_key = 'fithub:youtube:' + hashlib.sha256(query.lower().encode('utf-8')).hexdigest()
    cached = cache.get(cache_key)
    if cached is not None:
        return JsonResponse({'videos': cached})

    # Basic per-user burst protection; this is deliberately separate from the shared result cache.
    rate_key = f'fithub:youtube:rate:{request.user.pk}'
    count = cache.get(rate_key, 0)
    if count >= 8:
        return JsonResponse({'error': 'Please wait a minute before searching for more tutorials.'}, status=429)
    cache.set(rate_key, count + 1, 60)

    params = urlencode({
        'part': 'snippet',
        'type': 'video',
        'maxResults': 6,
        'safeSearch': 'strict',
        'q': query,
        'videoEmbeddable': 'true',
        'key': api_key,
    })
    req = Request(
        'https://www.googleapis.com/youtube/v3/search?' + params,
        headers={'Accept': 'application/json', 'User-Agent': 'FitHub/1.0'},
    )
    try:
        with urlopen(req, timeout=8) as response:  # nosec
            payload = json.loads(response.read().decode('utf-8'))
    except HTTPError as exc:
        if exc.code == 403:
            return JsonResponse({'error': 'YouTube search is temporarily unavailable. Please try again later.'}, status=503)
        return JsonResponse({'error': 'Could not load tutorials right now. Please try again.'}, status=502)
    except (URLError, TimeoutError, ValueError):
        return JsonResponse({'error': 'Could not connect to YouTube. Please try again.'}, status=502)

    videos = []
    for item in payload.get('items', []):
        video_id = item.get('id', {}).get('videoId', '')
        snippet = item.get('snippet', {})
        if not video_id or len(video_id) != 11:
            continue
        thumbnails = snippet.get('thumbnails', {})
        thumbnail = (thumbnails.get('medium') or thumbnails.get('default') or {}).get('url', '')
        videos.append({
            'id': video_id,
            'title': snippet.get('title', 'Exercise tutorial'),
            'channel': snippet.get('channelTitle', ''),
            'thumbnail': thumbnail,
        })
    cache.set(cache_key, videos, 60 * 60 * 24)
    return JsonResponse({'videos': videos})


@login_required
def workout_detail(request, pk):
    workout = _attach_set_forms(_own_workout(request, pk))
    form = ExerciseForm(workout=workout)
    exercises = list(workout.exercises.all())
    total_sets = sum(exercise.set_entries.count() for exercise in exercises)
    completed_sets = sum(
        exercise.set_entries.filter(is_completed=True).count() for exercise in exercises
    )
    return render(request, 'tracker/workout_detail.html', {
        'workout': workout,
        'form': form,
        'total_sets': total_sets,
        'completed_sets': completed_sets,
        'progress_percent': round(completed_sets * 100 / total_sets) if total_sets else 0,
    })


@login_required
def workout_edit(request, pk):
    workout = _own_workout(request, pk)
    form = WorkoutForm(request.POST or None, instance=workout, owner=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Workout updated.')
        return redirect('tracker:workout-detail', pk=workout.pk)
    return render(request, 'tracker/workout_form.html', {'form': form, 'title': 'Edit workout', 'workout': workout})


@login_required
def workout_delete(request, pk):
    workout = _own_workout(request, pk)
    if request.method == 'POST':
        workout.delete()
        messages.success(request, 'Workout deleted.')
        return redirect('tracker:workout-list')
    return render(request, 'tracker/confirm_delete.html', {'workout': workout})


@login_required
@require_POST
def exercise_add(request, pk):
    workout = _own_workout(request, pk)
    form = ExerciseForm(request.POST, workout=workout)
    if form.is_valid():
        exercise = form.save(commit=False)
        exercise.workout = workout
        exercise.save()
        ExerciseSet.objects.bulk_create([
            ExerciseSet(
                exercise=exercise,
                set_number=number,
                reps=exercise.reps,
                weight_kg=exercise.weight_kg,
                is_completed=False,
            )
            for number in range(1, exercise.sets + 1)
        ])
        messages.success(request, f'Added {exercise.name}. Complete each set as you train.')
        return redirect('tracker:workout-detail', pk=workout.pk)
    workout = _attach_set_forms(workout)
    return render(request, 'tracker/workout_detail.html', {
        'workout': workout, 'form': form,
    }, status=400)


@login_required
@require_POST
def exercise_delete(request, pk, exercise_pk):
    workout = _own_workout(request, pk)
    get_object_or_404(Exercise, pk=exercise_pk, workout=workout).delete()
    return redirect('tracker:workout-detail', pk=workout.pk)


@login_required
@require_POST
def exercise_set_add(request, pk, exercise_pk):
    workout = _own_workout(request, pk)
    form = ExerciseSetAddForm(request.POST, prefix=f'add-set-{exercise_pk}')
    with transaction.atomic():
        exercise = get_object_or_404(Exercise.objects.select_for_update(), pk=exercise_pk, workout=workout)
        if exercise.set_entries.count() >= 50:
            messages.error(request, 'An exercise can have at most 50 sets.')
            return redirect('tracker:workout-detail', pk=workout.pk)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.exercise = exercise
            entry.set_number = (exercise.set_entries.order_by('-set_number').values_list('set_number', flat=True).first() or 0) + 1
            if entry.set_number > 50:
                messages.error(request, 'No more set numbers are available for this exercise.')
            else:
                entry.save()
                messages.success(request, f'Set {entry.set_number} added.')
        else:
            messages.error(request, 'Please check the set details and try again.')
    return redirect('tracker:workout-detail', pk=workout.pk)


@login_required
@require_POST
def exercise_set_edit(request, pk, exercise_pk, set_pk):
    workout = _own_workout(request, pk)
    exercise = get_object_or_404(Exercise, pk=exercise_pk, workout=workout)
    entry = get_object_or_404(ExerciseSet, pk=set_pk, exercise=exercise)
    form = ExerciseSetForm(request.POST, instance=entry, prefix=f'set-{entry.pk}')
    if form.is_valid():
        form.save()
        messages.success(request, f'Set {entry.set_number} updated.')
        return redirect('tracker:workout-detail', pk=workout.pk)
    workout = _attach_set_forms(workout, form)
    return render(request, 'tracker/workout_detail.html', {
        'workout': workout,
        'form': ExerciseForm(workout=workout),
    }, status=400)


@login_required
@require_POST
def exercise_set_delete(request, pk, exercise_pk, set_pk):
    workout = _own_workout(request, pk)
    with transaction.atomic():
        exercise = get_object_or_404(Exercise.objects.select_for_update(), pk=exercise_pk, workout=workout)
        entry = get_object_or_404(ExerciseSet, pk=set_pk, exercise=exercise)
        entry.delete()
        # Keep visible set numbering contiguous after a removal.
        for number, item in enumerate(exercise.set_entries.order_by('set_number', 'id'), start=1):
            if item.set_number != number:
                item.set_number = number
                item.save(update_fields=['set_number'])
    messages.success(request, 'Set removed.')
    return redirect('tracker:workout-detail', pk=workout.pk)


@login_required
def weight(request):
    form = WeightForm(request.POST or None, initial={'date': timezone.localdate()})
    if request.method == 'POST' and form.is_valid():
        BodyMetric.objects.update_or_create(
            owner=request.user, date=form.cleaned_data['date'], defaults={'weight_kg': form.cleaned_data['weight_kg']})
        messages.success(request, 'Weight saved.')
        return redirect('tracker:weight')
    days = _days(request, 90)
    profile = profile_for(request.user)
    entries = BodyMetric.objects.filter(owner=request.user)
    page = Paginator(entries, PAGE_SIZE).get_page(request.GET.get('page'))
    return render(request, 'tracker/weight.html', {
        'form': form, 'page': page, 'days': days, 'periods': PERIODS,
        'chart': analytics.line_chart(analytics.weight_points(request.user, days), target=profile.target_weight_kg),
        'target': profile.target_weight_kg})


@login_required
@require_POST
def weight_delete(request, pk):
    get_object_or_404(BodyMetric, pk=pk, owner=request.user).delete()
    return redirect('tracker:weight')


def _parse_day(value):
    try:
        day = datetime.strptime(value or '', '%Y-%m-%d').date()
    except ValueError:
        return timezone.localdate()
    return min(day, timezone.localdate())


@login_required
def meals(request):
    day = _parse_day(request.GET.get('date'))
    form = MealForm(request.POST or None, owner=request.user, initial={'date': day})
    if request.method == 'POST' and form.is_valid():
        meal = form.save(commit=False)
        meal.owner = request.user
        meal.save()
        messages.success(request, f'Logged {meal.name}.')
        return redirect(f"{reverse('tracker:meals')}?date={meal.date:%Y-%m-%d}")
    profile = profile_for(request.user)
    items = Meal.objects.filter(owner=request.user, date=day)
    totals = analytics.day_totals(request.user, day)
    return render(request, 'tracker/meals.html', {
        'form': form, 'day': day, 'items': items, 'totals': totals, 'target': profile.calorie_target,
        'percent': analytics.percent(totals['calories'], profile.calorie_target),
        'prev': day - timedelta(days=1), 'next': day + timedelta(days=1) if day < timezone.localdate() else None})


@login_required
@require_POST
def meal_delete(request, pk):
    meal = get_object_or_404(Meal, pk=pk, owner=request.user)
    day = meal.date
    meal.delete()
    return redirect(f"{reverse('tracker:meals')}?date={day:%Y-%m-%d}")


@login_required
def export_csv(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="fithub-workouts.csv"'
    writer = csv.writer(response)
    writer.writerow(['date', 'workout', 'minutes', 'exercise', 'set_number', 'reps', 'weight_kg', 'is_completed', 'is_warmup'])
    workouts = Workout.objects.filter(owner=request.user).prefetch_related('exercises__set_entries').order_by('date', 'id')
    for workout in workouts:
        exercises = list(workout.exercises.all())
        if not exercises:
            writer.writerow([workout.date, _csv_safe(workout.name), workout.duration_min, '', '', '', '', '', ''])
            continue
        for exercise in exercises:
            sets = list(exercise.set_entries.all())
            if not sets:
                writer.writerow([workout.date, _csv_safe(workout.name), workout.duration_min,
                                 _csv_safe(exercise.name), '', '', '', '', ''])
                continue
            for entry in sets:
                writer.writerow([
                    workout.date, _csv_safe(workout.name), workout.duration_min, _csv_safe(exercise.name),
                    entry.set_number, entry.reps, entry.weight_kg, entry.is_completed, entry.is_warmup,
                ])
    return response
