from django.contrib import admin
from .models import ProgressRecord

@admin.register(ProgressRecord)
class ProgressRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'weight', 'body_fat')
    list_filter = ('date',)
