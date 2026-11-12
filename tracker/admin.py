from django.contrib import admin

from .models import BodyMetric, Exercise, Meal, Profile, Workout


class ExerciseInline(admin.TabularInline):
    model = Exercise
    extra = 0


@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'date', 'duration_min')
    list_filter = ('date',)
    search_fields = ('name', 'owner__username')
    inlines = [ExerciseInline]


admin.site.register(Profile)
admin.site.register(BodyMetric)
admin.site.register(Meal)
