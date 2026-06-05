from django.contrib import admin

from .models import FitnessIcon, InspirationCategory, MotivationQuote


@admin.register(InspirationCategory)
class InspirationCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'display_order')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('display_order',)


@admin.register(FitnessIcon)
class FitnessIconAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'nationality', 'is_featured', 'display_order')
    list_filter = ('category', 'is_featured')
    search_fields = ('name', 'nickname', 'bio')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('display_order', 'name')


@admin.register(MotivationQuote)
class MotivationQuoteAdmin(admin.ModelAdmin):
    list_display = ('author', 'category', 'is_featured', 'created_at')
    list_filter = ('category', 'is_featured')
    search_fields = ('text', 'author')
