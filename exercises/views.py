from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST

from core.utils import get_current_goal
from goals.models import Goal
from .goal_logic import adjust_reps_sets_for_body_type, filter_exercises_by_goal
from .models import Exercise, ExerciseCompletion


def _parse_steps(text):
    if not text:
        return {'setup_steps': [], 'movement_steps': []}
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    setup = []
    movement = []
    joined = '\n'.join(lines)
    if 'setup:' in joined.lower() or 'movement:' in joined.lower():
        curr = None
        for line in lines:
            if line.lower().startswith('setup:'):
                curr = 'setup'
                content = line.split(':', 1)[1].strip()
                if content:
                    setup.append(content)
                continue
            if line.lower().startswith('movement:'):
                curr = 'movement'
                content = line.split(':', 1)[1].strip()
                if content:
                    movement.append(content)
                continue
            if curr == 'setup':
                setup.append(line)
            elif curr == 'movement':
                movement.append(line)
            else:
                movement.append(line)
    else:
        if not lines:
            return {'setup_steps': [], 'movement_steps': []}
        split_at = max(1, len(lines) // 3)
        setup = lines[:split_at]
        movement = lines[split_at:]
    return {'setup_steps': setup, 'movement_steps': movement}


def _build_recommended_slugs(user, selected_goal: str, focus_areas: list) -> set:
    if not selected_goal or selected_goal == 'my_plan':
        return set()
    ex_qs = Exercise.objects.all()
    ex_list = [
        {
            'name': ex.name,
            'slug': ex.slug,
            'category': ex.category,
            'equipment': ex.equipment,
            'goal': ex.goal,
        }
        for ex in ex_qs
    ]
    filtered = filter_exercises_by_goal(ex_list, selected_goal, focus_areas)
    return {item.get('slug') for item in filtered}


def _resolve_goal_for_user(request: HttpRequest):
    active_goal = None
    selected_goal = None
    focus_areas: list = []

    if hasattr(request, 'user') and getattr(request.user, 'is_authenticated', False):
        active_goal = (
            Goal.objects.filter(user=request.user).order_by('-id').first()
        )
        if active_goal:
            selected_goal = active_goal.goal_type
            focus_areas = active_goal.focus_areas or []
            if not active_goal.assigned_exercises.exists():
                active_goal.sync_assigned_exercises()
        else:
            current_goal_obj = get_current_goal(request)
            if current_goal_obj:
                active_goal = current_goal_obj
                selected_goal = current_goal_obj.goal_type
                focus_areas = current_goal_obj.focus_areas or []
            else:
                prof = getattr(request.user, 'profile', None)
                raw = getattr(prof, 'selected_goal', None)
                if raw:
                    from core.utils import map_profile_goal_to_goal_type
                    selected_goal = map_profile_goal_to_goal_type(raw)

    if request.GET.get('selectedGoal'):
        selected_goal = request.GET.get('selectedGoal')

    return active_goal, selected_goal, focus_areas


def index(request):
    return render(request, 'index.html')


def exercise_list(request):
    active_goal, selected_goal, focus_areas = _resolve_goal_for_user(request)

    body_type = None
    if hasattr(request.user, 'profile'):
        body_type = getattr(request.user.profile, 'body_type', None)

    recommended_slugs = _build_recommended_slugs(
        request.user if hasattr(request, 'user') else None,
        selected_goal,
        focus_areas,
    )

    exercises_qs = Exercise.objects.all()
    show_all = selected_goal == 'my_plan'
    exercises = []
    for ex in exercises_qs:
        parsed = _parse_steps(ex.steps)
        reps_sets = adjust_reps_sets_for_body_type(
            ex.default_reps, ex.default_sets, body_type
        )
        exercises.append({
            'name': ex.name,
            'slug': ex.slug,
            'description': ex.description,
            'category': ex.get_category_display(),
            'category_slug': ex.category,
            'difficulty': ex.get_difficulty_display(),
            'equipment': ex.equipment or 'Bodyweight',
            'target_muscles': ex.target_muscles,
            'image_url': ex.image_url,
            'video_url': ex.video_url,
            'setup_steps': parsed['setup_steps'],
            'movement_steps': parsed['movement_steps'],
            'form_tips': ex.form_tips or ex.safety or '',
            'reps': reps_sets['reps'],
            'sets': reps_sets['sets'],
            'duration_min': ex.duration_min,
            'calories_per_set': ex.calories_per_set,
            'recommended': (ex.slug in recommended_slugs) and not show_all,
        })

    exercises.sort(key=lambda item: (not item.get('recommended', False), item['name']))

    context = {
        'exercises': exercises,
        'active_goal': active_goal,
        'selected_goal': selected_goal,
        'focus_areas': focus_areas,
        'show_all': show_all,
        'total_count': len(exercises),
        'recommended_count': sum(1 for e in exercises if e['recommended']),
    }
    return render(request, 'exercises/exercise_list.html', context)


def exercise_detail(request, slug):
    exercise = get_object_or_404(Exercise, slug=slug)
    parsed = _parse_steps(exercise.steps)
    body_type = None
    if hasattr(request.user, 'profile'):
        body_type = getattr(request.user.profile, 'body_type', None)
    reps_sets = adjust_reps_sets_for_body_type(
        exercise.default_reps, exercise.default_sets, body_type
    )

    user = request.user if getattr(request.user, 'is_authenticated', False) else None
    is_completed_today = False
    completion_count = 0
    if user:
        from django.utils import timezone
        today = timezone.now().date()
        is_completed_today = ExerciseCompletion.objects.filter(
            user=user,
            exercise=exercise,
            date=today,
        ).exists()
        completion_count = ExerciseCompletion.objects.filter(
            user=user,
            exercise=exercise,
        ).count()

    context = {
        'exercise': exercise,
        'setup_steps': parsed['setup_steps'],
        'movement_steps': parsed['movement_steps'],
        'reps': reps_sets['reps'],
        'sets': reps_sets['sets'],
        'is_completed_today': is_completed_today,
        'completion_count': completion_count,
    }
    return render(request, 'exercises/exercise_detail.html', context)


@login_required
@require_POST
def quick_complete(request, slug):
    exercise = get_object_or_404(Exercise, slug=slug)
    completion = ExerciseCompletion.objects.create(
        user=request.user,
        exercise=exercise,
        reps=exercise.default_reps,
        hold_time_sec=None,
        notes='',
    )

    stats, _ = _get_or_create_stats(request.user)
    from django.utils import timezone
    today = timezone.now().date()
    if not stats.last_workout_date or stats.last_workout_date != today:
        stats.total_workouts += 1
        stats.last_workout_date = today
        stats.update_streak()
    else:
        stats.save()

    messages.success(
        request,
        f'Great work! {exercise.name} logged. Keep it up!',
    )
    next_url = request.POST.get('next') or reverse('exercise-detail', args=[slug])
    return redirect(next_url)


def _get_or_create_stats(user):
    from progress.models import UserWorkoutStats
    return UserWorkoutStats.objects.get_or_create(user=user)
