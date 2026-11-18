from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

KINDS = [('breakfast', 'Breakfast'), ('lunch', 'Lunch'), ('dinner', 'Dinner'), ('snack', 'Snack')]


def today():
    return timezone.localdate()


class Profile(models.Model):
    """A person's goals. Created on first visit to the goals page."""

    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='fit_profile')
    calorie_target = models.PositiveIntegerField(default=2200, validators=[MinValueValidator(800), MaxValueValidator(6000)])

    age = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(13), MaxValueValidator(100)]
    )
    height_cm = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True,
        validators=[MinValueValidator(120), MaxValueValidator(230)],
    )
    starting_weight_kg = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True,
        validators=[MinValueValidator(30), MaxValueValidator(300)],
    )
    sex_for_calculation = models.CharField(
        max_length=20, blank=True,
        choices=[
            ('female', 'Female'), ('male', 'Male'),
            ('other', 'Other / prefer not to say'),
        ],
    )
    activity_level = models.CharField(
        max_length=20, blank=True,
        choices=[
            ('sedentary', 'Mostly sitting / little exercise'),
            ('light', 'Light activity (1–3 days/week)'),
            ('moderate', 'Moderate activity (3–5 days/week)'),
            ('very_active', 'Very active (6–7 days/week)'),
        ],
    )
    nutrition_goal = models.CharField(
        max_length=12, blank=True, default='maintain',
        choices=[('fat_loss', 'Fat loss'), ('maintain', 'Weight maintenance'), ('muscle_gain', 'Muscle gain')],
    )
    training_type = models.CharField(
        max_length=12, blank=True,
        choices=[
            ('strength', 'Strength / muscle building'),
            ('cardio', 'Cardio / endurance'),
            ('mixed', 'Mixed strength and cardio'),
            ('general', 'General fitness'),
        ],
    )
    weekly_workout_target = models.PositiveSmallIntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(14)])
    target_weight_kg = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True,
        validators=[MinValueValidator(Decimal('30')), MaxValueValidator(300)],
    )

    def __str__(self):
        return f'Goals of {self.owner}'


class Workout(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='workouts')
    date = models.DateField(default=today)
    name = models.CharField(max_length=80)
    duration_min = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(600)])
    notes = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-id']
        indexes = [models.Index(fields=['owner', 'date'])]

    def __str__(self):
        return f'{self.name} ({self.date})'

    @property
    def volume_kg(self):
        """Total volume from completed individual sets only."""
        return sum(
            (
                entry.reps * entry.weight_kg
                for exercise in self.exercises.all()
                for entry in exercise.set_entries.all()
                if entry.is_completed
            ),
            Decimal('0'),
        )


class Exercise(models.Model):
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE, related_name='exercises')
    name = models.CharField(max_length=80)
    sets = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(50)])
    reps = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(500)])
    weight_kg = models.DecimalField(max_digits=5, decimal_places=1, default=0,
                                    validators=[MinValueValidator(0), MaxValueValidator(1000)])

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.name


class ExerciseSet(models.Model):
    """One performed (or planned) set belonging to a workout exercise."""

    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='set_entries')
    set_number = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(50)]
    )
    reps = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(500)]
    )
    weight_kg = models.DecimalField(
        max_digits=5, decimal_places=1, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(1000)],
    )
    is_completed = models.BooleanField(default=False)
    is_warmup = models.BooleanField(default=False)

    class Meta:
        ordering = ['set_number', 'id']
        constraints = [
            models.UniqueConstraint(fields=['exercise', 'set_number'], name='unique_exercise_set_number'),
        ]

    def __str__(self):
        return f'{self.exercise.name} · set {self.set_number}'


class BodyMetric(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='body_metrics')
    date = models.DateField(default=today)
    weight_kg = models.DecimalField(max_digits=4, decimal_places=1,
                                    validators=[MinValueValidator(Decimal('20')), MaxValueValidator(Decimal('400'))])

    class Meta:
        ordering = ['-date']
        constraints = [models.UniqueConstraint(fields=['owner', 'date'], name='one_weight_per_day')]

    def __str__(self):
        return f'{self.weight_kg} kg on {self.date}'


class Meal(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='meals')
    date = models.DateField(default=today)
    kind = models.CharField(max_length=10, choices=KINDS, default='lunch')
    name = models.CharField(max_length=80)
    calories = models.PositiveSmallIntegerField(validators=[MaxValueValidator(5000)])
    protein_g = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(500)])
    carbs_g = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(1000)])
    fat_g = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(500)])

    class Meta:
        ordering = ['date', 'id']
        indexes = [models.Index(fields=['owner', 'date'])]

    def __str__(self):
        return f'{self.name} ({self.calories} kcal)'


def profile_for(user):
    profile, _ = Profile.objects.get_or_create(owner=user)
    return profile


class ResearchCacheEntry(models.Model):
    """Django database-cache row for shared, short-lived research results."""

    cache_key = models.CharField(max_length=255, primary_key=True)
    value = models.TextField()
    expires = models.DateTimeField(db_index=True)

    class Meta:
        db_table = 'fithub_research_cache'
