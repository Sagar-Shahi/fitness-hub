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
    focus_areas = models.JSONField(blank=True, default=list)
    assigned_exercises = models.ManyToManyField('exercises.Exercise', blank=True, related_name='assigned_goals')
    progress_percent = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} – {self.get_goal_type_display()}"

    def get_suggested_exercises(self):
        from django.db.models import Q
        from exercises.models import Exercise

        if self.goal_type == 'calisthenics':
            query = (
                Q(equipment__in=['', 'bodyweight', 'none']) |
                Q(name__icontains='progression') |
                Q(name__icontains='pull') |
                Q(name__icontains='push') |
                Q(category__in=['core', 'back', 'arms', 'chest', 'shoulders'])
            )
        elif self.goal_type in ['strength', 'muscle_gain', 'lean_bulk', 'recomp']:
            query = (
                Q(goal__in=['strength', 'hypertrophy']) |
                Q(category__in=['legs', 'back', 'chest', 'shoulders'])
            )
        elif self.goal_type == 'fat_loss':
            query = (
                Q(goal='weight_loss') |
                Q(category__in=['cardio', 'legs', 'core'])
            )
        elif self.goal_type == 'lean_athletic':
            query = (
                Q(goal__in=['strength', 'hypertrophy']) |
                Q(category__in=['back', 'shoulders', 'core', 'legs'])
            )
        else:
            query = Q()

        exercises = Exercise.objects.filter(query) if query else Exercise.objects.all()

        focus_map = {
            'shoulders': 'shoulders',
            'back': 'back',
            'core': 'core',
            'legs': 'legs',
        }
        focus_filters = [focus_map.get(area.lower()) for area in self.focus_areas or [] if focus_map.get(area.lower())]
        if focus_filters:
            focused = exercises.filter(category__in=focus_filters)
            if focused.exists():
                exercises = focused

        return exercises.distinct()

    def sync_assigned_exercises(self):
        self.assigned_exercises.set(self.get_suggested_exercises())
