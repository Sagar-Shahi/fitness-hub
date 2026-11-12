"""Fill a development database with a demo account and eight weeks of believable activity.

    python manage.py seed_demo

Only works when DJANGO_DEBUG=True, so a demo account with a known password can never exist on a live site.
"""
import random
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from tracker.models import BodyMetric, Exercise, Meal, Profile, Workout

DEMO_PASSWORD = 'demo-password-2026'  # nosec B105

SESSIONS = {
    'Push day': [('Bench press', 4, 8, 60), ('Overhead press', 3, 8, 35), ('Triceps pushdown', 3, 12, 25)],
    'Pull day': [('Barbell row', 4, 8, 55), ('Lat pulldown', 3, 10, 45), ('Biceps curl', 3, 12, 14)],
    'Leg day': [('Squat', 4, 6, 80), ('Romanian deadlift', 3, 8, 70), ('Leg press', 3, 12, 120)],
}
MEALS = [
    ('breakfast', 'Oats, banana and peanut butter', 480, 18, 70, 14),
    ('lunch', 'Dal, rice and vegetable curry', 720, 24, 110, 18),
    ('snack', 'Yoghurt and fruit', 220, 12, 30, 5),
    ('dinner', 'Paneer tikka, roti and salad', 650, 34, 55, 28),
]


class Command(BaseCommand):
    help = 'Create a demo user ("demo") with sample workouts, meals, weight and plans. Development only.'

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('seed_demo only runs when DJANGO_DEBUG=True.')
        rng = random.Random(2026)  # nosec B311
        user, _ = get_user_model().objects.get_or_create(username='demo', defaults={'email': 'demo@example.com'})
        user.set_password(DEMO_PASSWORD)
        user.save()
        user.workouts.all().delete()
        user.meals.all().delete()
        user.body_metrics.all().delete()
        Profile.objects.update_or_create(owner=user, defaults={
            'calorie_target': 2200, 'weekly_workout_target': 4, 'target_weight_kg': Decimal('79.0')})

        today = timezone.localdate()
        names = list(SESSIONS)
        weight = Decimal('82.6')
        for ago in range(56, -1, -1):
            day = today - timedelta(days=ago)
            if day.weekday() in (0, 1, 3, 4) and rng.random() < 0.9:
                name = names[(day.toordinal()) % 3]
                workout = Workout.objects.create(owner=user, date=day, name=name, duration_min=rng.randint(40, 70))
                progress = Decimal(str(round((56 - ago) * 0.08, 1)))
                Exercise.objects.bulk_create([
                    Exercise(workout=workout, name=n, sets=s, reps=r, weight_kg=Decimal(w) + progress)
                    for n, s, r, w in SESSIONS[name]])
            if ago % 2 == 0 or rng.random() < 0.3:
                weight -= Decimal(str(round(rng.uniform(-0.1, 0.25), 1)))
                BodyMetric.objects.create(owner=user, date=day, weight_kg=weight.quantize(Decimal('0.1')))
            if ago > 0 or rng.random() < 0.8:
                for kind, name, kcal, p, c, f in MEALS:
                    if rng.random() < 0.92:
                        Meal.objects.create(owner=user, date=day, kind=kind, name=name,
                                            calories=kcal + rng.randint(-60, 80), protein_g=p, carbs_g=c, fat_g=f)
        call_command('seed_plans', stdout=self.stdout)
        self.stdout.write(f'Demo data ready. Log in as "demo" with password "{DEMO_PASSWORD}".')
