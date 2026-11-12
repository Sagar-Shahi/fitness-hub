from django.contrib import admin

from .models import ApiKey


@admin.register(ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):
    """The key itself is never stored, so there is nothing secret to see here. Revoking is allowed."""

    list_display = ('name', 'owner', 'prefix', 'created_at', 'last_used_at', 'revoked_at')
    readonly_fields = ('owner', 'name', 'prefix', 'created_at', 'last_used_at')
    exclude = ('key_hash',)
    list_select_related = ('owner',)

    def has_add_permission(self, request):
        return False
