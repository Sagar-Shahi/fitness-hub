"""Build a personalized context for the bot's reply.

Pulls the user's actual app data — last workout, streak, active goal, BMI
bucketed, store activity — so the bot can deliver personalized
motivational replies and relevant app tips.

This is *read-only*; the bot never modifies any of this data.
"""

from datetime import timedelta
from decimal import Decimal


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def build_user_context(user) -> dict:
    """Return a dict of user-state facts the bot can use.

    Empty dict if the user isn't logged in. Keys:
        - name:              first name or username
        - goal:              selected_goal code, or None
        - goal_label:        human-readable goal
        - bmi_bucket:        'under' | 'normal' | 'over' | 'obese' | None
        - streak_days:       consecutive days with at least one completion
        - days_since_last:   days since last logged workout (None if never)
        - total_completions: total logged exercises
        - total_minutes:     total minutes trained
        - recent_exercises:  list of recent exercise names
        - has_orders:        bool, has placed at least one order
        - has_active_goal:   bool, has chosen a goal
        - is_new:            bool, no completions yet
    """
    if user is None or not getattr(user, 'is_authenticated', False):
        return {}

    ctx = {
        'name': (user.first_name or user.username or '').strip(),
        'goal': None,
        'goal_label': None,
        'bmi_bucket': None,
        'streak_days': 0,
        'days_since_last': None,
        'total_completions': 0,
        'total_minutes': 0,
        'recent_exercises': [],
        'has_orders': False,
        'has_active_goal': False,
        'is_new': True,
    }

    profile = getattr(user, 'profile', None)
    if profile:
        ctx['goal'] = profile.selected_goal or None
        ctx['has_active_goal'] = bool(profile.selected_goal)
        ctx['bmi_bucket'] = _bmi_bucket(profile.height_ft, profile.weight_kg)

    # Workout stats (read-only)
    try:
        from exercises.models import ExerciseCompletion
        from django.utils import timezone
        from django.db.models import Sum, F

        completions = ExerciseCompletion.objects.filter(user=user)
        ctx['total_completions'] = completions.count()
        if ctx['total_completions'] == 0:
            ctx['is_new'] = True
        else:
            ctx['is_new'] = False

            # Total minutes (sum of exercise.duration_min across completions)
            total_min = (
                completions
                .select_related('exercise')
                .aggregate(
                    total=Sum('exercise__duration_min'),
                )['total']
            )
            ctx['total_minutes'] = int(total_min or 0)

            # Recent exercise names (last 5)
            recent = list(
                completions
                .select_related('exercise')
                .order_by('-date', '-id')[:5]
            )
            ctx['recent_exercises'] = [c.exercise.name for c in recent]

            # Days since last workout
            last = completions.order_by('-date').first()
            if last:
                last_date = last.date
                if last_date:
                    delta = (timezone.now().date() - last_date).days
                    ctx['days_since_last'] = max(0, delta)

            # Streak: consecutive days with at least one completion
            ctx['streak_days'] = _compute_streak(completions)
    except Exception:
        pass

    # Order history
    try:
        from store.models import Order
        ctx['has_orders'] = Order.objects.filter(user=user).exists()
    except Exception:
        pass

    return ctx


def _bmi_bucket(height_ft, weight_kg) -> str | None:
    """Bucket BMI into under/normal/over/obese. Returns None if not enough data."""
    if not height_ft or not weight_kg:
        return None
    try:
        h_m = float(height_ft) * 0.3048
        if h_m <= 0:
            return None
        bmi = float(weight_kg) / (h_m * h_m)
    except (TypeError, ValueError, ZeroDivisionError):
        return None
    if bmi < 18.5:
        return 'under'
    if bmi < 25:
        return 'normal'
    if bmi < 30:
        return 'over'
    return 'obese'


def _compute_streak(completions_qs) -> int:
    """Return count of consecutive days back from today (or yesterday) with a completion."""
    from django.utils import timezone
    from collections import OrderedDict
    today = timezone.now().date()
    by_day = set(completions_qs.values_list('date', flat=True))
    if not by_day:
        return 0
    # If user didn't train today, allow streak ending yesterday
    start = today if today in by_day else (today - timedelta(days=1))
    if start not in by_day:
        return 0
    streak = 0
    d = start
    while d in by_day:
        streak += 1
        d = d - timedelta(days=1)
    return streak


# ---------------------------------------------------------------------------
# Context-aware message builders
# ---------------------------------------------------------------------------

def greeting_for_context(ctx: dict) -> str:
    """Build a personalized greeting line for a logged-in user."""
    if not ctx:
        return (
            "Hey! I'm the Fitness Hub bot. I can help with exercises, "
            "the app, and general fitness stuff. What's up?"
        )
    name = ctx.get('name') or 'friend'
    streak = ctx.get('streak_days', 0)
    days_off = ctx.get('days_since_last')

    if ctx.get('is_new'):
        return (
            f"Hey {name}! Welcome to Fitness Hub. I'm the bot around here — "
            "I can help you set a goal, find your first workout, or just "
            "show you how things work. What sounds good?"
        )
    if streak >= 3:
        return (
            f"Hey {name}! Good to see you — {streak} days and going strong. 🔥 "
            "What are we working on today?"
        )
    if days_off is not None and days_off >= 3:
        return (
            f"Hey {name}. I see it's been a bit since your last log — "
            "no pressure at all. Just wanted to say it's never too late to pick it back up. "
            "I'm here whenever you're ready."
        )
    return (
        f"Hey {name}! What are we thinking today? "
        "I can suggest a workout, answer a question, or just chat."
    )


def motivation_for_context(ctx: dict) -> str:
    """Build a personalized motivational reply based on user state."""
    if not ctx:
        return (
            "Honestly? Showing up is most of the battle. "
            "Open the Workout Library, pick anything, and give it a go. "
            "I'll be here when you're done."
        )
    streak = ctx.get('streak_days', 0)
    days_off = ctx.get('days_since_last')
    completions = ctx.get('total_completions', 0)
    goal = ctx.get('goal_label') or 'your goal'
    recent = ctx.get('recent_exercises', [])

    if ctx.get('is_new'):
        return (
            "Welcome! The single best thing you can do right now is log your first "
            "workout. Pick any beginner exercise in the Workout Library, tap "
            "**Mark Complete & Log**, and boom — you've started. That's all it takes."
        )

    if streak >= 7:
        return (
            f"{streak} days — that's real consistency, not luck. "
            f"Keep trusting the process and your {goal} work will keep building. "
            "Open the Workout Library and grab whatever's next on your list."
        )

    if streak >= 3:
        return (
            f"Nice — {streak} days in a row! Keep it simple today: "
            f"pick something you enjoyed this week, do a few sets, log it. Easy win."
        )

    if days_off is not None and days_off >= 5:
        return (
            f"Hey, it's been {days_off} days and that's totally fine. "
            f"A 15-minute session is all it takes to get back in motion. "
            f"One exercise, a few sets, log it. Starting again is the win."
        )

    if days_off is not None and days_off >= 1:
        return (
            f"You've logged {completions} sessions so far — that's real progress. "
            f"Last one was {days_off} day(s) ago. Today's a good day to add to that."
        )

    if completions >= 10:
        return (
            f"You've logged {completions} sessions. Solid foundation. "
            f"Might be time to try a harder variation, add a set, or explore a new "
            f"category. Keep challenging yourself."
        )

    return (
        "The most important step is the one you take right now. Open the Workout Library, "
        "find something that catches your eye, and start with one set. You might surprise yourself."
    )


def next_action_for_context(ctx: dict) -> str:
    """Suggest the user's next best action in the app."""
    if not ctx:
        return (
            "If you're new: start at `/goals/` to pick a primary goal, then open "
            "`/exercises/` to find your first workout."
        )
    if ctx.get('is_new'):
        return (
            "Best next step: **pick a goal** in `/goals/`, then open `/exercises/` "
            "and try your first session. The whole app tunes to your goal from there."
        )
    if not ctx.get('has_active_goal'):
        return (
            "You don't have an active goal set — that's why the app can't tune "
            "recommendations to you. Open `/goals/` and pick one. Takes 30 seconds."
        )
    if ctx.get('days_since_last') is not None and ctx['days_since_last'] >= 3:
        return (
            f"Your last log was {ctx['days_since_last']} days ago. "
            "Go to `/exercises/`, pick a beginner exercise, and log one set. "
            "That's the move right now."
        )
    if ctx.get('streak_days', 0) >= 1:
        return (
            f"You're on a {ctx['streak_days']}-day streak. "
            "Well done — keep it up! Open `/exercises/` and add another session today."
        )
    return (
        "Open `/exercises/`, pick something tagged with your active goal, "
        "and log it. Or hit `/diet/` to see today's macro targets."
    )


# Map goal code to human label
GOAL_LABELS = {
    'general':     'general fitness',
    'strength':    'strength',
    'hypertrophy': 'muscle growth',
    'endurance':   'endurance',
    'mobility':    'mobility',
    'flexibility': 'flexibility',
    'weight_loss': 'fat loss',
}


def hydrate_goal_label(ctx: dict) -> dict:
    if ctx and ctx.get('goal'):
        ctx['goal_label'] = GOAL_LABELS.get(ctx['goal'], ctx['goal'])
    return ctx
