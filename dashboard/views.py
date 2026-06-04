from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from goals.models import Goal
from progress.models import ProgressRecord
from exercises.models import ExerciseCompletion
from core.utils import get_current_goal


def get_next_exercise(goal):
    if not goal:
        return None
    assigned = goal.assigned_exercises.all()
    if assigned.exists():
        return assigned.first()
    return None


def compute_goal_readiness(goal, user):
    if not goal:
        return 0
    if goal.progress_percent:
        return min(100, max(0, goal.progress_percent))

    logs = ProgressRecord.objects.filter(user=user, goal=goal)
    assigned = goal.assigned_exercises.count()
    if assigned == 0:
        return 0
    completed_ratio = min(1.0, logs.count() / max(1, assigned))
    return int(completed_ratio * 100)


def get_focus_alignment_message(request):
    """Get dynamic focus alignment message for dashboard display."""
    from progress.views import generate_focus_alignment_message
    goal = get_current_goal(request)
    return generate_focus_alignment_message(request.user, goal)


@login_required
def index(request):
    goal = get_current_goal(request)
    next_exercise = get_next_exercise(goal)
    readiness = compute_goal_readiness(goal, request.user)

    # Get focus alignment message
    focus_alignment = get_focus_alignment_message(request)

    # Get user workout stats
    stats = getattr(request.user, 'workout_stats', None)

    return render(
        request,
        'dashboard/index.html',
        {
            'goal': goal,
            'next_exercise': next_exercise,
            'readiness': readiness,
            'focus_alignment': focus_alignment,
            'stats': stats,
        },
    )
