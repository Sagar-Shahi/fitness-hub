from typing import Optional
from django.http import HttpRequest
from django.contrib.auth.models import User
from goals.models import Goal


def map_profile_goal_to_goal_type(selected_goal: Optional[str]) -> Optional[str]:
    if not selected_goal:
        return None
    key = selected_goal.lower()
    mapping = {
        'calisthenics_body': 'calisthenics',
        'calisthenics': 'calisthenics',
        'v_taper': 'lean_athletic',
        'lean_athletic': 'lean_athletic',
        'weight_loss': 'fat_loss',
        'fat_loss': 'fat_loss',
        'general_fitness': 'general',
        'general': 'general',
        'muscle_gain': 'muscle_gain',
        'lean_bulk': 'lean_bulk',
        'recomp': 'recomp',
        'strength': 'strength',
        'my_plan': None,
    }
    for prefix, goal_type in mapping.items():
        if key.startswith(prefix):
            return goal_type
    return 'general'


def sync_goal_from_profile(user: User, profile) -> Optional[Goal]:
    if not profile or not profile.selected_goal:
        return Goal.objects.filter(user=user).order_by('-id').first()
    goal_type = map_profile_goal_to_goal_type(profile.selected_goal)
    if not goal_type:
        return Goal.objects.filter(user=user).order_by('-id').first()
    goal, created = Goal.objects.get_or_create(
        user=user,
        goal_type=goal_type,
        defaults={'description': 'Auto-synced goal from profile selection.'}
    )
    if created or not goal.assigned_exercises.exists():
        goal.sync_assigned_exercises()
    return goal


def get_current_goal(request: HttpRequest) -> Optional[Goal]:
    user = request.user
    profile = getattr(user, 'profile', None)
    return sync_goal_from_profile(user, profile)