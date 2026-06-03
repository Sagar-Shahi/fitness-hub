from django.conf import settings
from django.db import models
from django.utils import timezone
from datetime import timedelta


class ProgressRecord(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='progress')
    goal = models.ForeignKey('goals.Goal', on_delete=models.SET_NULL, null=True, blank=True, related_name='progress_logs')
    date = models.DateField()
    weight = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    body_fat = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    waist = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    chest = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    arm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} — {self.date}"


class UserWorkoutStats(models.Model):
    """Tracks user workout statistics including streaks and motivation metrics."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='workout_stats')
    total_workouts = models.PositiveIntegerField(default=0)
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_workout_date = models.DateField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Workout Stats"
        verbose_name_plural = "User Workout Stats"

    def __str__(self):
        return f"{self.user.username} — Total: {self.total_workouts}, Streak: {self.current_streak}"

    def update_streak(self):
        """Update user streak based on last workout date."""
        from exercises.models import ExerciseCompletion
        if not self.last_workout_date:
            return

        today = timezone.now().date()
        days_since_last = (today - self.last_workout_date).days

        if days_since_last == 0:
            # Workout today, continue or start streak
            self.current_streak += 1
        elif days_since_last == 1:
            # Workout yesterday, continue streak
            self.current_streak += 1
        else:
            # Streak broken, reset
            self.current_streak = 1

        # Update longest streak
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak

        self.save()
