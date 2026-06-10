"""Signal handlers that award XP / progress quests for in-app actions.

Each handler is wrapped in a try/except so a bad signal never breaks the
underlying flow (logging a workout should never 500 because of gamification).
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from . import services as svc
from . import models as gm

logger = logging.getLogger(__name__)


@receiver(post_save, sender='exercises.ExerciseCompletion')
def on_workout_completed(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        user = instance.user
        svc.award_xp(
            user, svc.XP_WORKOUT, source='workout',
            description=f'Logged {instance.exercise.name}',
        )
        svc.progress_quest(user, 'workouts_logged', 1)
        svc.progress_quest(user, 'workout_minutes', instance.exercise.duration_min or 0)
        svc.check_and_unlock_badges(user)
    except Exception:
        logger.exception('gamification: on_workout_completed failed')


@receiver(post_save, sender='goals.Goal')
def on_goal_created(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        user = instance.user
        svc.award_xp(
            user, svc.XP_GOAL_CREATED, source='goal',
            description=f'New goal: {instance.get_goal_type_display()}',
        )
        svc.check_and_unlock_badges(user)
    except Exception:
        logger.exception('gamification: on_goal_created failed')


@receiver(post_save, sender='diet.NutritionRecord')
def on_meal_logged(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        user = instance.user
        svc.award_xp(
            user, svc.XP_MEAL_LOGGED, source='meal',
            description='Logged a meal',
        )
        svc.progress_quest(user, 'meals_logged', 1)
        svc.check_and_unlock_badges(user)
    except Exception:
        logger.exception('gamification: on_meal_logged failed')


@receiver(post_save, sender='store.Order')
def on_order_placed(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        user = instance.user
        svc.award_xp(
            user, svc.XP_ORDER_PLACED, source='order',
            description=f'Order {instance.order_number}',
        )
        svc.progress_quest(user, 'orders_placed', 1)
        svc.check_and_unlock_badges(user)
    except Exception:
        logger.exception('gamification: on_order_placed failed')
