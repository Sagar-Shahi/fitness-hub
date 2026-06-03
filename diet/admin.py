from django.contrib import admin
from .models import NutritionRecord

@admin.register(NutritionRecord)
class NutritionRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'calories')
    list_filter = ('date',)
