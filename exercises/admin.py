from django.contrib import admin
from .models import Exercise


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'difficulty')
    list_filter = ('category', 'difficulty')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'category', 'difficulty', 'goal',
                       'description', 'target_muscles', 'equipment',
                       'steps', 'form_tips', 'breathing', 'common_mistakes', 'safety'),
        }),
        ('Stats', {
            'fields': ('default_reps', 'default_sets', 'duration_min', 'calories_per_set'),
        }),
        ('Image & Video', {
            'fields': ('image', 'image_url', 'video_url'),
            'description': 'Upload an image or provide an external URL. Uploaded image takes priority.',
        }),
    )
