from django.contrib import admin
from .models import Exercise


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'difficulty')
    prepopulated_fields = {'slug': ('name',)}
from django.contrib import admin

# Register your models here.
