from django.urls import path

from . import views

app_name = 'shop'

urlpatterns = [
    path('app/plans/', views.plans, name='plans'),
    path('app/plans/mine/', views.my_plans, name='my-plans'),
    path('app/plans/<slug:slug>/', views.plan_detail, name='plan-detail'),
    path('app/cart/', views.cart, name='cart'),
    path('app/cart/add/<slug:slug>/', views.cart_add, name='cart-add'),
    path('app/cart/remove/<slug:slug>/', views.cart_remove, name='cart-remove'),
    path('app/checkout/', views.checkout, name='checkout'),
    path('app/orders/', views.orders, name='orders'),
    path('app/orders/<str:reference>/', views.order_detail, name='order-detail'),
]
