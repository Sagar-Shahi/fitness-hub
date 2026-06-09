from django.contrib import admin
from .models import (
    PlayerStats, Badge, UserBadge, Quest, UserQuest, XPEvent, StreakShieldUse,
)


@admin.register(PlayerStats)
class PlayerStatsAdmin(admin.ModelAdmin):
    list_display = ('user', 'level_display', 'xp', 'streak_shields', 'coins')
    list_filter = ('streak_shields',)
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('last_active',)
    actions = ['reset_stats']

    @admin.display(description='Level', ordering='xp')
    def level_display(self, obj):
        return obj.level

    @admin.action(description='Reset selected players')
    def reset_stats(self, request, queryset):
        for stats in queryset:
            stats.reset_for_testing()


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('icon', 'name', 'tier', 'xp_reward', 'code', 'is_secret')
    list_filter = ('tier', 'is_secret')
    search_fields = ('name', 'code', 'description')
    prepopulated_fields = {'code': ('name',)}


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge', 'unlocked_at')
    list_filter = ('badge__tier',)
    search_fields = ('user__username', 'badge__name')
    date_hierarchy = 'unlocked_at'


@admin.register(Quest)
class QuestAdmin(admin.ModelAdmin):
    list_display = ('icon', 'name', 'frequency', 'target_type',
                    'target_count', 'xp_reward', 'coin_reward', 'weight')
    list_filter = ('frequency', 'target_type')
    search_fields = ('name', 'code', 'description')
    prepopulated_fields = {'code': ('name',)}


@admin.register(UserQuest)
class UserQuestAdmin(admin.ModelAdmin):
    list_display = ('user', 'quest', 'progress', 'target', 'status',
                    'assigned_date', 'expires_at')
    list_filter = ('status', 'quest__frequency')
    search_fields = ('user__username', 'quest__name')
    date_hierarchy = 'assigned_date'


@admin.register(XPEvent)
class XPEventAdmin(admin.ModelAdmin):
    list_display = ('user', 'source', 'amount', 'description', 'created_at')
    list_filter = ('source',)
    search_fields = ('user__username', 'description')
    date_hierarchy = 'created_at'


@admin.register(StreakShieldUse)
class StreakShieldUseAdmin(admin.ModelAdmin):
    list_display = ('user', 'used_on', 'reason', 'created_at')
    search_fields = ('user__username', 'reason')
    date_hierarchy = 'used_on'
