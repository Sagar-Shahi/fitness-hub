from django.contrib import admin
from .models import Goal

@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ('user', 'goal_type', 'progress_percent', 'target_weight')
    list_filter = ('goal_type',)
