from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import timedelta

from .models import ProgressRecord, UserWorkoutStats
from exercises.models import ExerciseCompletion, Exercise
from goals.models import Goal
from .forms import ExerciseCompletionForm

CALISTHENICS_BENCHMARKS = {
    'pull-up': 8,
    'chin-up': 8,
    'push-up': 20,
    'dip': 12,
    'hollow hold': 30,
}

# Volume targets by focus area (sets x reps per week)
FOCUS_VOLUME_TARGETS = {
    'upper_body': 150,
    'lower_body': 120,
    'core': 100,
    'pull_strength': 80,
    'push_strength': 80,
    'mobility': 60,
}


def map_profile_goal(selected_goal):
    if not selected_goal:
        return None
    key = selected_goal.lower()
    if key.startswith('calisthenics'):
        return 'calisthenics'
    if key.startswith('lean_athletic'):
        return 'lean_athletic'
    if key.startswith('muscle_gain'):
        return 'muscle_gain'
    if key.startswith('lean_bulk'):
        return 'lean_bulk'
    if key.startswith('fat_loss'):
        return 'fat_loss'
    if key.startswith('recomp'):
        return 'recomp'
    if key.startswith('strength'):
        return 'strength'
    if key.startswith('my_plan'):
        return None
    return 'general'


def get_current_goal(request):
    selected_goal = None
    if hasattr(request.user, 'profile'):
        selected_goal = getattr(request.user.profile, 'selected_goal', None)
    goal_type = map_profile_goal(selected_goal)
    if goal_type:
        goal, created = Goal.objects.get_or_create(
            user=request.user,
            goal_type=goal_type,
            defaults={'description': 'Auto-synced goal from profile selection.'}
        )
        if created or not goal.assigned_exercises.exists():
            goal.sync_assigned_exercises()
        return goal

    return Goal.objects.filter(user=request.user).order_by('-id').first()


def finish_exercise(user, exercise, reps=None, hold_time_sec=None, notes=''):
    """
    Handler to record completed exercise and update user workout statistics.
    
    Args:
        user: User instance
        exercise: Exercise instance
        reps: Number of reps completed
        hold_time_sec: Hold time in seconds
        notes: Optional notes about the exercise
    
    Returns:
        ExerciseCompletion instance
    """
    # Create exercise completion record
    completion = ExerciseCompletion.objects.create(
        user=user,
        exercise=exercise,
        reps=reps,
        hold_time_sec=hold_time_sec,
        notes=notes,
    )

    # Update user workout stats
    stats, created = UserWorkoutStats.objects.get_or_create(user=user)
    today = timezone.now().date()

    # Update total workouts if this is the first exercise today
    if not stats.last_workout_date or stats.last_workout_date != today:
        stats.total_workouts += 1
        stats.last_workout_date = today
        stats.update_streak()
    else:
        stats.save()

    return completion


def calculate_volume_trend(user, focus_area, days=7):
    """
    Calculate volume trend (Sets x Reps) for a specific focus area over time.
    
    Args:
        user: User instance
        focus_area: One of the GOAL_FOCUS_CHOICES
        days: Number of days to look back (default 7)
    
    Returns:
        {
            'total_volume': total_sets_x_reps,
            'target_volume': target_for_focus_area,
            'completion_percent': percentage_of_target,
            'daily_breakdown': [(date, volume), ...],
            'trend_direction': 'up' | 'down' | 'stable'
        }
    """
    from exercises.models import ExerciseCompletion
    from users.models import Profile

    profile = getattr(user, 'profile', None)
    if not profile or profile.goal_focus != focus_area:
        focus_area = profile.goal_focus if profile else 'upper_body'

    # Map focus areas to exercise categories
    focus_to_categories = {
        'upper_body': ['chest', 'back', 'shoulders', 'arms'],
        'lower_body': ['legs'],
        'core': ['core'],
        'pull_strength': ['back', 'arms'],
        'push_strength': ['chest', 'shoulders', 'arms'],
        'mobility': ['mobility'],
    }

    categories = focus_to_categories.get(focus_area, ['chest', 'back', 'shoulders'])

    # Get completions for the period
    start_date = timezone.now().date() - timedelta(days=days)
    completions = ExerciseCompletion.objects.filter(
        user=user,
        exercise__category__in=categories,
        date__gte=start_date,
    ).order_by('date')

    # Calculate total volume
    total_volume = sum(
        (comp.reps or 1) * (1 if not comp.hold_time_sec else 0) + (comp.hold_time_sec or 0)
        for comp in completions
    )

    # Daily breakdown
    daily_breakdown = {}
    for comp in completions:
        volume = (comp.reps or 1) + (comp.hold_time_sec or 0) / 30
        daily_breakdown[comp.date] = daily_breakdown.get(comp.date, 0) + volume

    daily_list = sorted(daily_breakdown.items())

    # Calculate trend direction
    trend_direction = 'stable'
    if len(daily_list) >= 2:
        first_half_avg = sum(v for d, v in daily_list[:len(daily_list)//2]) / max(1, len(daily_list)//2)
        second_half_avg = sum(v for d, v in daily_list[len(daily_list)//2:]) / max(1, len(daily_list) - len(daily_list)//2)
        if second_half_avg > first_half_avg * 1.1:
            trend_direction = 'up'
        elif second_half_avg < first_half_avg * 0.9:
            trend_direction = 'down'

    target = FOCUS_VOLUME_TARGETS.get(focus_area, 100)
    completion_percent = min(100, int((total_volume / max(1, target)) * 100))

    return {
        'total_volume': int(total_volume),
        'target_volume': target,
        'completion_percent': completion_percent,
        'daily_breakdown': daily_list,
        'trend_direction': trend_direction,
    }


def calculate_weekly_completion_percent(user, goal=None):
    """
    Calculate completion percentage for weekly target.
    
    Args:
        user: User instance
        goal: Optional Goal instance
    
    Returns:
        {
            'percent': completion_percent,
            'exercises_completed': number_completed,
            'exercises_assigned': number_assigned,
        }
    """
    if not goal:
        goal = get_current_goal(get_current_goal.__self__)

    if not goal:
        return {'percent': 0, 'exercises_completed': 0, 'exercises_assigned': 0}

    assigned_count = goal.assigned_exercises.count()
    if assigned_count == 0:
        return {'percent': 0, 'exercises_completed': 0, 'exercises_assigned': 0}

    # Count unique exercises completed this week
    start_date = timezone.now().date() - timedelta(days=7)
    completed_exercises = ExerciseCompletion.objects.filter(
        user=user,
        exercise__in=goal.assigned_exercises.all(),
        date__gte=start_date,
    ).values('exercise').distinct().count()

    percent = min(100, int((completed_exercises / assigned_count) * 100))

    return {
        'percent': percent,
        'exercises_completed': completed_exercises,
        'exercises_assigned': assigned_count,
    }


def generate_focus_alignment_message(user, goal=None):
    """
    Generate dynamic focus alignment message based on volume trends and progress.
    
    Args:
        user: User instance
        goal: Optional Goal instance
    
    Returns:
        {
            'message': message_text,
            'message_type': 'alert' | 'info' | 'success' | 'warning',
            'volume_stats': volume_trend_data,
            'weekly_stats': weekly_completion_data,
        }
    """
    if not goal:
        from django.http import HttpRequest
        request = HttpRequest()
        request.user = user
        goal = get_current_goal(request)

    if not goal:
        return {
            'message': 'Set up a goal to get personalized feedback!',
            'message_type': 'info',
            'volume_stats': {},
            'weekly_stats': {},
        }

    profile = getattr(user, 'profile', None)
    focus_area = profile.goal_focus if profile else 'upper_body'

    volume_stats = calculate_volume_trend(user, focus_area, days=7)
    weekly_stats = calculate_weekly_completion_percent(user, goal)

    completion_percent = volume_stats['completion_percent']
    trend = volume_stats['trend_direction']

    message = ""
    message_type = "info"

    # Generate message based on volume completion
    if completion_percent < 50:
        message = f"You haven't hit your {focus_area.replace('_', ' ').title()} target this week. "
        focus_to_exercise = {
            'upper_body': 'Push-ups or Dips',
            'lower_body': 'Squats or Lunges',
            'core': 'Hollow Hold or Leg Raises',
            'pull_strength': 'Pull-ups or Chin-ups',
            'push_strength': 'Push-ups or Dips',
            'mobility': 'Mobility drills',
        }
        suggestion = focus_to_exercise.get(focus_area, 'compound exercises')
        message += f"Focus on {suggestion} tomorrow!"
        message_type = "warning"

    elif completion_percent >= 50 and completion_percent < 100:
        if trend == 'up':
            percent_increase = int((volume_stats['total_volume'] / max(1, volume_stats['target_volume'] * 0.5)) * 10)
            message = f"Great job! Your {focus_area.replace('_', ' ').lower()} volume is up {percent_increase}% this week. Keep it up!"
            message_type = "success"
        elif trend == 'down':
            message = f"You're at {completion_percent}% of your weekly {focus_area.replace('_', ' ').lower()} target. Let's push harder this week!"
            message_type = "alert"
        else:
            message = f"You're making steady progress on your {focus_area.replace('_', ' ').lower()} goal. Keep going!"
            message_type = "info"

    else:  # >= 100%
        if trend == 'up':
            message = f"Excellent! You've exceeded your {focus_area.replace('_', ' ').lower()} target by {completion_percent - 100}%. You're crushing it!"
            message_type = "success"
        else:
            message = f"You've hit your {focus_area.replace('_', ' ').lower()} target! Maintain this consistency!"
            message_type = "success"

    return {
        'message': message,
        'message_type': message_type,
        'volume_stats': volume_stats,
        'weekly_stats': weekly_stats,
    }


def build_focus_suggestions(goal, completions):
    suggestions = []
    if not goal:
        return suggestions

    if goal.goal_type == 'calisthenics':
        for keyword, target in CALISTHENICS_BENCHMARKS.items():
            max_reps = max(
                (comp.reps or 0)
                for comp in completions
                if comp.exercise and keyword in comp.exercise.name.lower()
            ) if completions else 0
            if max_reps < target:
                suggestions.append(
                    f"Focus on: Increasing {keyword.title()} volume to reach your Calisthenics goal."
                )
        if not suggestions:
            suggestions.append(
                'Your Calisthenics progress is on track. Keep building strength and consistency.'
            )

    return suggestions


@login_required
def index(request):
    goal = get_current_goal(request)
    completions = ExerciseCompletion.objects.filter(user=request.user).order_by('-date')[:50]

    assigned_exercises = goal.assigned_exercises.all() if goal else Exercise.objects.none()
    focus_suggestions = build_focus_suggestions(goal, completions)

    # Generate dynamic focus alignment message
    focus_alignment = generate_focus_alignment_message(request.user, goal)

    # Get user workout stats
    stats = getattr(request.user, 'workout_stats', None)

    return render(
        request,
        'progress/index.html',
        {
            'completions': completions,
            'goal': goal,
            'assigned_exercises': assigned_exercises,
            'focus_suggestions': focus_suggestions,
            'focus_alignment': focus_alignment,
            'stats': stats,
        },
    )


@login_required
def log_exercise(request, slug):
    exercise = get_object_or_404(Exercise, slug=slug)
    if request.method == 'POST':
        form = ExerciseCompletionForm(request.POST)
        if form.is_valid():
            reps = form.cleaned_data.get('reps')
            hold_time_sec = form.cleaned_data.get('hold_time_sec')
            notes = form.cleaned_data.get('notes', '')
            
            # Use finish_exercise handler
            completion = finish_exercise(
                user=request.user,
                exercise=exercise,
                reps=reps,
                hold_time_sec=hold_time_sec,
                notes=notes
            )
            return redirect('exercise-detail', slug=slug)
    else:
        form = ExerciseCompletionForm()
    return render(request, 'progress/log_exercise.html', {'form': form, 'exercise': exercise})
