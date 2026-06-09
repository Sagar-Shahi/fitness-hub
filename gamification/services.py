"""XP, level, badge, and quest service layer.

All gamification side-effects (awarding XP, checking for badge unlocks,
progressing quests, levelling up) flow through this module so the rules
are centralized and unit-testable.

Public functions:
    - award_xp(user, amount, source, description) -> dict
    - get_or_create_stats(user) -> PlayerStats
    - check_and_unlock_badges(user) -> list[UserBadge]
    - progress_quest(user, target_type, amount) -> list[UserQuest]
    - generate_daily_quests(user) -> list[UserQuest]
    - claim_quest(user_quest) -> dict
    - get_player_summary(user) -> dict
"""

from __future__ import annotations

from datetime import timedelta
from typing import Iterable

from django.conf import settings
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.utils import timezone

from . import models as gm


# ---------------------------------------------------------------------------
# XP source constants — keep them tiny so callers can read the intent.
# ---------------------------------------------------------------------------

XP_WORKOUT = 25
XP_WORKOUT_FIRST_OF_DAY = 15  # bonus
XP_DIFFERENT_EXERCISE_SAME_DAY = 10  # bonus per unique exercise in a day
XP_GOAL_CREATED = 50
XP_MEAL_LOGGED = 10
XP_ORDER_PLACED = 30
XP_STREAK_DAY = 10
XP_STREAK_7 = 100
XP_STREAK_30 = 500
XP_BADGE_UNLOCKED = 0  # badges can carry their own xp_reward
XP_QUEST_COMPLETED = 0  # quest xp_reward is on the Quest itself


# ---------------------------------------------------------------------------
# Player stats
# ---------------------------------------------------------------------------

def get_or_create_stats(user) -> gm.PlayerStats:
    """Return the user's PlayerStats, creating it on first access."""
    stats, _ = gm.PlayerStats.objects.get_or_create(user=user)
    return stats


@transaction.atomic
def award_xp(user, amount: int, source: str = 'other', description: str = '') -> dict:
    """Add (or subtract) XP for a user and write an XPEvent audit row.

    Returns a dict with `stats`, `leveled_up` (bool), `levels_gained` (int),
    `new_level` (int), and `new_title` (str). Idempotent on negative
    amounts: never lets XP go below 0.
    """
    if user is None or not getattr(user, 'is_authenticated', False):
        return {'stats': None, 'leveled_up': False, 'levels_gained': 0}

    if amount == 0:
        stats = get_or_create_stats(user)
        return {
            'stats': stats,
            'leveled_up': False,
            'levels_gained': 0,
            'new_level': stats.level,
            'new_title': stats.title,
        }

    stats = get_or_create_stats(user)
    old_level = stats.level

    if amount < 0:
        applied = -min(stats.xp, -amount)
        new_xp = stats.xp + applied  # applied is negative
    else:
        applied = amount
        new_xp = stats.xp + amount

    stats.xp = new_xp
    stats.last_active = timezone.now()
    stats.save(update_fields=['xp', 'last_active'])

    gm.XPEvent.objects.create(
        user=user, source=source, amount=applied, description=description[:200],
    )

    new_level = stats.level
    leveled_up = new_level > old_level
    return {
        'stats': stats,
        'leveled_up': leveled_up,
        'levels_gained': new_level - old_level,
        'new_level': new_level,
        'new_title': stats.title,
        'applied': applied,
    }


def grant_coins(user, amount: int, source: str = 'other') -> int:
    if user is None or amount <= 0:
        return 0
    stats = get_or_create_stats(user)
    stats.coins += amount
    stats.save(update_fields=['coins'])
    return amount


# ---------------------------------------------------------------------------
# Badges
# ---------------------------------------------------------------------------

# Hard-coded rules per badge code. Kept inline so the seed script and
# runtime checks stay in sync.
BADGE_RULES = {
    'first_step':   lambda ctx: ctx['total_workouts'] >= 1,
    'week_warrior': lambda ctx: ctx['longest_streak'] >= 7,
    'iron_month':   lambda ctx: ctx['longest_streak'] >= 30,
    'century_club': lambda ctx: ctx['total_workouts'] >= 100,
    'goal_setter':  lambda ctx: ctx['has_goal'],
    'variety_pack': lambda ctx: ctx['distinct_exercises'] >= 10,
    'lvl_5':        lambda ctx: ctx['level'] >= 5,
    'lvl_10':       lambda ctx: ctx['level'] >= 10,
    'lvl_20':       lambda ctx: ctx['level'] >= 20,
    'lvl_50':       lambda ctx: ctx['level'] >= 50,
    'quest_hunter': lambda ctx: ctx['quests_completed'] >= 10,
    'iron_quest':   lambda ctx: ctx['weekly_quests_completed'] >= 4,
    'meal_logger':  lambda ctx: ctx['meals_logged'] >= 7,
    'shopper':      lambda ctx: ctx['orders_placed'] >= 1,
    'shiny_shopper': lambda ctx: ctx['orders_placed'] >= 5,
    'early_bird':   lambda ctx: ctx['early_workouts'] >= 1,
    'night_owl':    lambda ctx: ctx['night_workouts'] >= 1,
}


def _build_user_context(user) -> dict:
    """Aggregate everything we know about a user for badge-rule evaluation."""
    from exercises.models import ExerciseCompletion
    from goals.models import Goal
    from diet.models import NutritionRecord
    from store.models import Order

    completions = ExerciseCompletion.objects.filter(user=user)
    distinct = completions.values('exercise').distinct().count()
    total = completions.count()
    longest = getattr(getattr(user, 'workout_stats', None), 'longest_streak', 0) or 0

    # Early / late workouts based on date + time, where available.
    early = night = 0
    for c in completions.select_related('exercise')[:500]:
        # We don't store the time of completion in the model; if we did,
        # we'd bucket it here. For now we just count morning-tagged
        # exercises as a proxy.
        if c.exercise.name and 'morning' in c.exercise.name.lower():
            early += 1
        if c.exercise.name and 'night' in c.exercise.name.lower():
            night += 1

    stats = get_or_create_stats(user)
    completed_quests = gm.UserQuest.objects.filter(
        user=user, status__in=['completed', 'claimed'],
    ).count()
    weekly_quests = gm.UserQuest.objects.filter(
        user=user, status__in=['completed', 'claimed'], quest__frequency='weekly',
    ).count()

    return {
        'total_workouts': total,
        'distinct_exercises': distinct,
        'longest_streak': longest,
        'has_goal': Goal.objects.filter(user=user).exists(),
        'meals_logged': NutritionRecord.objects.filter(user=user).count(),
        'orders_placed': Order.objects.filter(user=user).count(),
        'level': stats.level,
        'quests_completed': completed_quests,
        'weekly_quests_completed': weekly_quests,
        'early_workouts': early,
        'night_workouts': night,
    }


@transaction.atomic
def check_and_unlock_badges(user) -> list:
    """Run all badge rules and unlock any newly-earned badges.

    Returns the list of newly-unlocked UserBadge rows (which can be empty).
    Awards the badge's xp_reward as a side-effect.
    """
    if user is None or not getattr(user, 'is_authenticated', False):
        return []

    already_unlocked = set(
        gm.UserBadge.objects.filter(user=user).values_list('badge__code', flat=True)
    )
    ctx = _build_user_context(user)
    newly_unlocked: list = []

    for badge in gm.Badge.objects.all():
        if badge.code in already_unlocked:
            continue
        rule = BADGE_RULES.get(badge.code)
        if not rule:
            continue
        try:
            if rule(ctx):
                ub = gm.UserBadge.objects.create(user=user, badge=badge)
                newly_unlocked.append(ub)
                if badge.xp_reward:
                    award_xp(
                        user, badge.xp_reward,
                        source='badge',
                        description=f'Unlocked {badge.name}',
                    )
        except Exception:
            # Never let a bad rule break the user flow.
            continue
    return newly_unlocked


# ---------------------------------------------------------------------------
# Quests
# ---------------------------------------------------------------------------

# Map a target_type to a way of computing "today's progress so far".
# All functions return a non-negative integer.
PROGRESS_FUNCS = {}


def _register(*target_types):
    def deco(fn):
        for t in target_types:
            PROGRESS_FUNCS[t] = fn
        return fn
    return deco


@_register('workouts_logged')
def _progress_workouts(user):
    from exercises.models import ExerciseCompletion
    today = timezone.localdate()
    return ExerciseCompletion.objects.filter(
        user=user, date=today,
    ).count()


@_register('meals_logged')
def _progress_meals(user):
    from diet.models import NutritionRecord
    today = timezone.localdate()
    return NutritionRecord.objects.filter(
        user=user, date=today,
    ).count()


@_register('orders_placed')
def _progress_orders(user):
    from store.models import Order
    today = timezone.localdate()
    return Order.objects.filter(
        user=user, created_at__date=today,
    ).count()


@_register('browse_exercises')
def _progress_browse(user):
    # We don't track page views in the DB; the chat/intent can call
    # progress_quest manually. Default 0.
    return 0


@_register('new_exercise_category')
def _progress_new_category(user):
    from exercises.models import ExerciseCompletion
    today = timezone.localdate()
    cats = ExerciseCompletion.objects.filter(
        user=user, date=today,
    ).values_list('exercise__category', flat=True).distinct()
    return len(set(cats))


@_register('workout_minutes')
def _progress_minutes(user):
    from exercises.models import ExerciseCompletion
    today = timezone.localdate()
    total = (
        ExerciseCompletion.objects
        .filter(user=user, date=today)
        .select_related('exercise')
        .aggregate(total=Sum('exercise__duration_min'))['total']
    )
    return int(total or 0)


@transaction.atomic
def progress_quest(user, target_type: str, amount: int = 1) -> list:
    """Increment progress on every active quest with this target_type.

    Returns the list of UserQuest rows that completed as a result.
    """
    if user is None or amount <= 0:
        return []
    completed: list = []
    now = timezone.now()
    quests = gm.UserQuest.objects.select_for_update().filter(
        user=user, status='active', quest__target_type=target_type,
    )
    for uq in quests:
        uq.progress = min(uq.target, uq.progress + amount)
        if uq.progress >= uq.target and uq.status == 'active':
            uq.status = 'completed'
            uq.completed_at = now
        uq.save()
        if uq.status == 'completed' and uq not in completed:
            completed.append(uq)
    return completed


@transaction.atomic
def generate_daily_quests(user, count: int = 3) -> list:
    """Spawn `count` daily quests for the user if none are active today.

    If there's already an active daily set, returns those instead.
    """
    today = timezone.localdate()
    existing = list(
        gm.UserQuest.objects.filter(
            user=user, assigned_date=today, quest__frequency='daily',
        ).select_related('quest')
    )
    if existing:
        return existing

    pool = list(
        gm.Quest.objects.filter(frequency='daily').order_by('?')[:max(count * 2, count)]
    )
    if not pool:
        return []

    chosen = pool[:count]
    expires = timezone.now() + timedelta(days=1)
    spawned = []
    for q in chosen:
        uq = gm.UserQuest.objects.create(
            user=user, quest=q, target=q.target_count,
            assigned_date=today, expires_at=expires,
        )
        spawned.append(uq)
    return spawned


@transaction.atomic
def claim_quest(user_quest) -> dict:
    """Mark a completed quest as claimed and award its XP / coins.

    Returns a dict with the awards.
    """
    if user_quest.status == 'claimed':
        return {'xp': 0, 'coins': 0, 'already_claimed': True}
    if user_quest.status != 'completed':
        return {'xp': 0, 'coins': 0, 'not_ready': True}

    quest = user_quest.quest
    xp = quest.xp_reward
    coins = quest.coin_reward
    user_quest.status = 'claimed'
    user_quest.claimed_at = timezone.now()
    user_quest.save(update_fields=['status', 'claimed_at'])

    if xp:
        award_xp(user_quest.user, xp, source='quest', description=f'Quest: {quest.name}')
    if coins:
        grant_coins(user_quest.user, coins)
    return {'xp': xp, 'coins': coins, 'already_claimed': False}


# ---------------------------------------------------------------------------
# Streak shields
# ---------------------------------------------------------------------------

def grant_streak_shield(user, count: int = 1, reason: str = '') -> int:
    """Award streak shields (e.g. for completing a 7-day streak)."""
    if user is None or count <= 0:
        return 0
    stats = get_or_create_stats(user)
    stats.streak_shields += count
    stats.save(update_fields=['streak_shields'])
    return count


def consume_streak_shield(user, reason: str = '') -> bool:
    """Burn one streak shield to protect today's streak. Returns True on success."""
    stats = get_or_create_stats(user)
    if stats.streak_shields <= 0:
        return False
    stats.streak_shields -= 1
    stats.save(update_fields=['streak_shields'])
    gm.StreakShieldUse.objects.create(user=user, reason=reason[:120])
    return True


# ---------------------------------------------------------------------------
# Summary for the UI
# ---------------------------------------------------------------------------

def get_player_summary(user) -> dict:
    """Aggregate everything the nav and profile page need to render the HUD."""
    if user is None or not getattr(user, 'is_authenticated', False):
        return {}

    stats = get_or_create_stats(user)
    today = timezone.localdate()
    daily_quests = list(
        gm.UserQuest.objects.filter(
            user=user, assigned_date=today, quest__frequency='daily',
        ).select_related('quest').order_by('id')
    )
    recent_badges = list(
        gm.UserBadge.objects.filter(user=user)
        .select_related('badge').order_by('-unlocked_at')[:5]
    )
    recent_xp = list(
        gm.XPEvent.objects.filter(user=user).order_by('-created_at')[:10]
    )
    return {
        'level': stats.level,
        'title': stats.title,
        'xp': stats.xp,
        'xp_into_level': stats.xp_into_level,
        'xp_to_next_level': stats.xp_to_next_level,
        'level_progress_percent': stats.level_progress_percent,
        'streak_shields': stats.streak_shields,
        'coins': stats.coins,
        'daily_quests': daily_quests,
        'recent_badges': recent_badges,
        'recent_xp': recent_xp,
    }
