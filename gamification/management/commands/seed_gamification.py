"""Seed the gamification catalog (badges + quest templates) on first run."""

from django.core.management.base import BaseCommand

from gamification.models import Badge, Quest


BADGES = [
    # code, name, description, icon, tier, xp_reward, is_secret
    ('first_step',   'First Step',         'Log your first workout',                    '👟', 'bronze',   25,  False),
    ('week_warrior', 'Week Warrior',       'Hit a 7-day streak',                        '🔥', 'silver',  150,  False),
    ('iron_month',   'Iron Month',         'Hit a 30-day streak',                       '🛡️', 'gold',    500,  False),
    ('century_club', 'Century Club',       'Log 100 workouts total',                    '💯', 'gold',    400,  False),
    ('goal_setter',  'Goal Setter',        'Create your first goal',                    '🎯', 'bronze',   50,  False),
    ('variety_pack', 'Variety Pack',       'Try 10 different exercises',                '🎲', 'silver',  100,  False),
    ('lvl_5',        'Rising Star',        'Reach level 5',                             '⭐', 'bronze',    0,  False),
    ('lvl_10',       'Gym Rat',            'Reach level 10',                            '🐀', 'silver',  200,  False),
    ('lvl_20',       'Iron Athlete',       'Reach level 20',                            '🏋️', 'gold',    500,  False),
    ('lvl_50',       'Living Legend',      'Reach level 50',                            '👑', 'mythic', 2500,  False),
    ('quest_hunter', 'Quest Hunter',       'Complete 10 daily quests',                  '📜', 'silver',  150,  False),
    ('iron_quest',   'Iron Quest',         'Complete 4 weekly quests',                  '🗓️', 'gold',    300,  False),
    ('meal_logger',  'Meal Master',        'Log 7 meals',                               '🥗', 'bronze',   50,  False),
    ('shopper',      'First Purchase',     'Place your first order',                    '🛒', 'bronze',   30,  False),
    ('shiny_shopper','Power Shopper',      'Place 5 orders',                            '💎', 'silver',  100,  False),
    ('early_bird',   'Early Bird',         'Log a morning workout',                     '🌅', 'bronze',   25,  False),
    ('night_owl',    'Night Owl',          'Log a late-night workout',                  '🌙', 'bronze',   25,  False),
]


QUESTS = [
    # code, name, description, icon, frequency, target_type, target_count, xp_reward, coin_reward, weight
    ('log_a_workout',   'Quick Set',        'Log any workout today',                  '💪', 'daily',   'workouts_logged',      1,  25, 0, 20),
    ('log_two_workouts','Double Trouble',   'Log 2 different exercises today',        '🥇', 'daily',   'workouts_logged',      2,  40, 0, 15),
    ('log_a_meal',      'Eat Clean',        'Log a meal today',                       '🥗', 'daily',   'meals_logged',         1,  15, 0, 20),
    ('browse_3',        'Scout It Out',     'Browse 3 exercises in the Workout Library', '🔍', 'daily', 'browse_exercises',     3,  15, 0, 10),
    ('try_new_cat',     'New Territory',    'Try an exercise from a category you haven\'t used today', '🗺️', 'daily', 'new_exercise_category', 1, 30, 0, 12),
    ('twenty_min',      'Twenty Minute',    'Train for 20 minutes total today',       '⏱️', 'daily',   'workout_minutes',     20,  35, 0, 12),
    ('forty_min',       'Forty Minute',     'Train for 40 minutes total today',       '🚀', 'daily',   'workout_minutes',     40,  60, 0, 8),
    ('place_order',     'Gear Up',          'Place an order in the store',            '🛒', 'daily',   'orders_placed',        1,  20, 0, 5),

    ('week_5',          'Five-Day Streak',  'Log 5 workouts this week',               '🔥', 'weekly',  'workouts_logged',      5, 100, 10, 10),
    ('week_10',         'Crusher Week',     'Log 10 workouts this week',              '💯', 'weekly',  'workouts_logged',     10, 200, 20, 8),
    ('week_minutes',    'Long Week',        'Train for 150+ minutes this week',       '⏳', 'weekly',  'workout_minutes',    150, 150, 15, 9),
    ('week_meals',      'Meal Prep Pro',    'Log 5 meals this week',                   '🍱', 'weekly',  'meals_logged',         5,  80, 5, 9),
]


class Command(BaseCommand):
    help = 'Seed the gamification catalog (badges and quest templates).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset', action='store_true',
            help='Delete existing catalog rows first.',
        )

    def handle(self, *args, **opts):
        if opts['reset']:
            Badge.objects.all().delete()
            Quest.objects.all().delete()
            self.stdout.write(self.style.WARNING('Cleared existing catalog.'))

        created_b = 0
        for code, name, desc, icon, tier, xp, secret in BADGES:
            _, was_created = Badge.objects.update_or_create(
                code=code,
                defaults={
                    'name': name, 'description': desc, 'icon': icon,
                    'tier': tier, 'xp_reward': xp, 'is_secret': secret,
                },
            )
            if was_created:
                created_b += 1
        self.stdout.write(self.style.SUCCESS(f'Badges: {created_b} created.'))

        created_q = 0
        for code, name, desc, icon, freq, target, count, xp, coins, weight in QUESTS:
            _, was_created = Quest.objects.update_or_create(
                code=code,
                defaults={
                    'name': name, 'description': desc, 'icon': icon,
                    'frequency': freq, 'target_type': target,
                    'target_count': count, 'xp_reward': xp,
                    'coin_reward': coins, 'weight': weight,
                },
            )
            if was_created:
                created_q += 1
        self.stdout.write(self.style.SUCCESS(f'Quests: {created_q} created.'))
        self.stdout.write(self.style.SUCCESS('Catalog seeded.'))
