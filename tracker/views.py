import csv
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
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
from .tutorials import search_youtube_videos
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


def _workout_detail_context(workout, form=None, bound_set_form=None):
    """Build one consistent context for the session page, including validation re-renders."""
    workout = _attach_set_forms(workout, bound_set_form)
    exercises = list(workout.exercises.all())
    set_entries = [entry for exercise in exercises for entry in exercise.set_entries.all()]
    total_sets = len(set_entries)
    completed_sets = sum(1 for entry in set_entries if entry.is_completed)
    return {
        'workout': workout,
        'form': form or ExerciseForm(workout=workout),
        'total_sets': total_sets,
        'completed_sets': completed_sets,
        'progress_percent': round(completed_sets * 100 / total_sets) if total_sets else 0,
    }


def _nutrition_plan_for(profile):
    latest_weight = BodyMetric.objects.filter(owner=profile.owner).first()
    current_weight = latest_weight.weight_kg if latest_weight else profile.starting_weight_kg
    from .nutrition import calculate_nutrition_targets
    return current_weight, calculate_nutrition_targets(profile, current_weight)


def _refresh_calorie_target(profile):
    from .nutrition import refresh_profile_calorie_target
    return refresh_profile_calorie_target(profile)


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
    current_weight, nutrition_plan = _nutrition_plan_for(profile)
    if request.method == 'POST' and form.is_valid():
        profile = form.save()
        current_weight, nutrition_plan = _refresh_calorie_target(profile)
        messages.success(request, 'Your fitness profile and nutrition targets have been saved.')
        return redirect('tracker:dashboard')
    items = (OrderItem.objects.filter(order__owner=request.user).select_related('plan', 'order')
             .order_by('-order__created_at'))
    seen, my_plans = set(), []
    for item in items:
        if item.plan_id not in seen:
            seen.add(item.plan_id)
            my_plans.append(item)
    return render(request, 'tracker/goals.html', {
        'form': form, 'my_plans': my_plans, 'nutrition_plan': nutrition_plan,
        'current_weight': current_weight,
    })


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
def focus_music_search(request):
    """Search public, embeddable YouTube videos for the signed-in user's Focus Audio player."""
    query = " ".join((request.GET.get("q") or "").split())
    if len(query) < 2 or len(query) > 100:
        return JsonResponse({"error": "Enter a song or artist name between 2 and 100 characters."}, status=400)
    return search_youtube_videos(
        request,
        query,
        cache_prefix="fithub:youtube:music:",
        max_results=8,
        cache_timeout=60 * 60 * 12,
        missing_key_message="In-app YouTube search is not configured yet. You can still paste a YouTube video link.",
    )


@login_required
def workout_detail(request, pk):
    workout = _own_workout(request, pk)
    return render(request, 'tracker/workout_detail.html', _workout_detail_context(workout))


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
    return render(
        request, 'tracker/workout_detail.html',
        _workout_detail_context(workout, form=form), status=400,
    )


@login_required
@require_POST
def exercise_delete(request, pk, exercise_pk):
    workout = _own_workout(request, pk)
    get_object_or_404(Exercise, pk=exercise_pk, workout=workout).delete()
    messages.success(request, 'Exercise and its sets removed.')
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
    return render(
        request, 'tracker/workout_detail.html',
        _workout_detail_context(workout, form=ExerciseForm(workout=workout), bound_set_form=form),
        status=400,
    )


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
        profile = profile_for(request.user)
        _refresh_calorie_target(profile)
        messages.success(request, 'Weight saved. Your nutrition estimates have been refreshed when your profile is complete.')
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
    _refresh_calorie_target(profile_for(request.user))
    messages.success(request, 'Weight entry deleted. Your nutrition estimate has been refreshed when your profile is complete.')
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
    current_weight, nutrition_plan = _nutrition_plan_for(profile)
    target = nutrition_plan['calories'] if nutrition_plan and nutrition_plan.get('calories') else profile.calorie_target
    items = Meal.objects.filter(owner=request.user, date=day)
    totals = analytics.day_totals(request.user, day)
    macro_remaining = None
    if nutrition_plan and nutrition_plan.get('calories'):
        macro_remaining = {
            'protein': max(0, nutrition_plan['protein_g'] - totals['protein']),
            'carbs': max(0, nutrition_plan['carbs_g'] - totals['carbs']),
            'fat': max(0, nutrition_plan['fat_g'] - totals['fat']),
        }
    return render(request, 'tracker/meals.html', {
        'form': form, 'day': day, 'items': items, 'totals': totals, 'target': target,
        'nutrition_plan': nutrition_plan, 'macro_remaining': macro_remaining,
        'percent': analytics.percent(totals['calories'], target),
        'prev': day - timedelta(days=1), 'next': day + timedelta(days=1) if day < timezone.localdate() else None})


@login_required
def meal_edit(request, pk):
    meal = get_object_or_404(Meal, pk=pk, owner=request.user)
    form = MealForm(request.POST or None, instance=meal, owner=request.user)
    if request.method == 'POST' and form.is_valid():
        updated = form.save()
        messages.success(request, f'Updated {updated.name}.')
        return redirect(f"{reverse('tracker:meals')}?date={updated.date:%Y-%m-%d}")
    return render(request, 'tracker/meal_edit.html', {'form': form, 'meal': meal})


@login_required
@require_POST
def meal_delete(request, pk):
    meal = get_object_or_404(Meal, pk=pk, owner=request.user)
    day = meal.date
    meal.delete()
    messages.success(request, 'Meal deleted.')
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
