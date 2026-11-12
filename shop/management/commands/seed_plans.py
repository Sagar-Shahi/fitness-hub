from decimal import Decimal

from django.core.management.base import BaseCommand

from shop.models import Plan

PLANS = [
    ('Beginner Full-Body 3x', 'workout', Decimal('9.00'), 'Three full-body sessions a week for your first 8 weeks.',
     "Schedule: Monday, Wednesday, Friday. Rest or walk on other days.\n\nSession A: Squat 3x8, Bench press 3x8, Row 3x10, Plank 3x30s.\nSession B: Deadlift 3x5, Overhead press 3x8, Lat pulldown 3x10, Side plank 3x20s.\n\nAdd 2.5 kg when you finish every set with good form. Warm up for 5 minutes first."),
    ('Push Pull Legs 6-Day', 'workout', Decimal('14.00'), 'A six-day split for lifters who already train and want more volume.',
     "Push: Bench press 4x6, Incline dumbbell press 3x10, Lateral raise 4x15, Triceps pushdown 3x12.\nPull: Barbell row 4x6, Pull-up 3x8, Face pull 3x15, Biceps curl 3x12.\nLegs: Squat 4x6, Romanian deadlift 3x8, Leg press 3x12, Calf raise 4x15.\n\nRun Push, Pull, Legs twice a week, one rest day. Deload every fifth week."),
    ('Home Bodyweight Plan', 'workout', Decimal('7.00'), 'No equipment. Four short sessions a week you can do in a living room.',
     "Four sessions of 30 minutes. Do each circuit 4 times with 60 seconds rest.\n\nCircuit 1: Push-ups 12, Split squats 10 each side, Plank 40s, Glute bridge 15.\nCircuit 2: Pike push-ups 8, Jump squats 12, Superman hold 30s, Mountain climbers 30s."),
    ('Balanced 2,000 kcal Week', 'diet', Decimal('8.00'), 'A seven-day, mostly vegetarian meal plan around 2,000 kcal a day.',
     "Daily pattern: Breakfast 450 kcal, Lunch 650, Snack 250, Dinner 650.\n\nExample day: Oats with banana and peanut butter. Dal, rice and a vegetable curry. Yoghurt and fruit. Paneer tikka with roti and salad.\n\nDrink water through the day. Adjust portions to your own needs; this is general guidance, not medical advice."),
]


class Command(BaseCommand):
    help = 'Create the sample plan catalogue if it does not exist yet.'

    def handle(self, *args, **options):
        created = 0
        for title, kind, price, summary, content in PLANS:
            _, was_created = Plan.objects.get_or_create(
                title=title, defaults={'kind': kind, 'price': price, 'summary': summary, 'content': content})
            created += was_created
        self.stdout.write(f'{created} plans created, {len(PLANS) - created} already existed.')
