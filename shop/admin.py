from django.contrib import admin

from .models import Order, OrderItem, Plan


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('title', 'kind', 'price', 'is_active')
    list_filter = ('kind', 'is_active')
    prepopulated_fields = {'slug': ('title',)}


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    readonly_fields = ('plan', 'title', 'price')

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('reference', 'owner', 'total', 'created_at')
    readonly_fields = ('reference', 'owner', 'total', 'created_at')
    inlines = [OrderItemInline]

    def has_add_permission(self, request):
        return False
