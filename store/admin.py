from django.contrib import admin
from .models import Category, Product, Cart, CartItem, Order, OrderItem


class ProductInline(admin.TabularInline):
    model = Product
    extra = 0
    fields = ('name', 'price', 'stock', 'is_active', 'is_featured')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'display_order', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductInline]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'category', 'price', 'compare_at_price',
        'stock', 'rating', 'is_featured', 'is_active',
    )
    list_filter = ('category', 'is_featured', 'is_active')
    search_fields = ('name', 'brand', 'sku', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('price', 'stock', 'is_featured', 'is_active')
    readonly_fields = ('created_at', 'updated_at')


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'added_at')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'session_key', 'created_at', 'updated_at')
    inlines = [CartItemInline]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'product_price', 'quantity')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number', 'user', 'full_name', 'total',
        'status', 'payment_method', 'created_at',
    )
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('order_number', 'user__username', 'full_name', 'email')
    readonly_fields = (
        'order_number', 'subtotal', 'shipping_cost', 'tax', 'total',
        'created_at', 'updated_at',
    )
    inlines = [OrderItemInline]
    list_editable = ('status',)
    date_hierarchy = 'created_at'
