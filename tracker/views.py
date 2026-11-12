import csv
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from . import analytics
from .forms import ExerciseForm, MealForm, ProfileForm, WeightForm, WorkoutForm
from .models import BodyMetric, Exercise, Meal, Workout, profile_for

PAGE_SIZE = 15
PERIODS = (7, 30, 90)


def _days(request, default=30):
    try:
        value = int(request.GET.get('days', default))
    except (TypeError, ValueError):
        return default
    return value if value in PERIODS else default


def _own_workout(request, pk):
    return get_object_or_404(Workout.objects.filter(owner=request.user).prefetch_related('exercises'), pk=pk)


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
    recent = (Workout.objects.filter(owner=request.user).prefetch_related('exercises')[:5])
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
def goals(request):
    profile = profile_for(request.user)
    form = ProfileForm(request.POST or None, instance=profile)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Goals saved.')
        return redirect('tracker:dashboard')
    return render(request, 'tracker/goals.html', {'form': form})


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
def workout_detail(request, pk):
    workout = _own_workout(request, pk)
    form = ExerciseForm(workout=workout)
    return render(request, 'tracker/workout_detail.html', {'workout': workout, 'form': form})


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
        messages.success(request, f'Added {exercise.name}.')
        return redirect('tracker:workout-detail', pk=workout.pk)
    return render(request, 'tracker/workout_detail.html', {'workout': workout, 'form': form}, status=400)


@login_required
@require_POST
def exercise_delete(request, pk, exercise_pk):
    workout = _own_workout(request, pk)
    get_object_or_404(Exercise, pk=exercise_pk, workout=workout).delete()
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
    writer.writerow(['date', 'workout', 'minutes', 'exercise', 'sets', 'reps', 'weight_kg'])
    for w in Workout.objects.filter(owner=request.user).prefetch_related('exercises').order_by('date', 'id'):
        rows = list(w.exercises.all()) or [None]
        for e in rows:
            writer.writerow([w.date, _csv_safe(w.name), w.duration_min,
                             _csv_safe(e.name) if e else '', e.sets if e else '', e.reps if e else '', e.weight_kg if e else ''])
    return response
