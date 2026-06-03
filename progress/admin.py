from django.contrib import admin
from .models import ProgressRecord, UserWorkoutStats
from exercises.models import ExerciseCompletion

@admin.register(ProgressRecord)
class ProgressRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'weight', 'body_fat')
    list_filter = ('date',)


@admin.register(UserWorkoutStats)
class UserWorkoutStatsAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_workouts', 'current_streak', 'longest_streak', 'last_workout_date')
    list_filter = ('updated_at',)
    search_fields = ('user__username',)
    readonly_fields = ('total_workouts', 'current_streak', 'longest_streak', 'updated_at')


@admin.register(ExerciseCompletion)
class ExerciseCompletionAdmin(admin.ModelAdmin):
    list_display = ('user', 'exercise', 'date', 'reps', 'hold_time_sec')
    list_filter = ('date', 'user', 'exercise')
