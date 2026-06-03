from django.conf import settings
from django.db import models

class Goal(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='goals')
    GOAL_CHOICES = [
        ('calisthenics', 'Calisthenics Physique'),
        ('lean_athletic', 'Lean Athletic Body'),
        ('muscle_gain', 'Muscle Gain'),
        ('lean_bulk', 'Lean Bulk'),
        ('fat_loss', 'Fat Loss'),
        ('recomp', 'Body Recomposition'),
        ('strength', 'Strength Training'),
        ('general', 'General Fitness'),
    ]
    goal_type = models.CharField(max_length=40, choices=GOAL_CHOICES)
    target_weight = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    timeline_weeks = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField(blank=True)
    progress_percent = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} – {self.get_goal_type_display()}"
