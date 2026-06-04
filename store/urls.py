from django.urls import path
from . import views

urlpatterns = [
    path('', views.store_home, name='store-home'),
    path('products/', views.product_list, name='store-product-list'),
    path('category/<slug:category_slug>/', views.product_list, name='store-category'),
    path('product/<slug:slug>/', views.product_detail, name='store-product-detail'),
    path('product/<slug:slug>/add/', views.add_to_cart, name='add-to-cart'),
    path('cart/', views.view_cart, name='view-cart'),
    path('cart/update/<int:item_id>/', views.update_cart, name='update-cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove-from-cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.order_history, name='order-history'),
    path('orders/<str:order_number>/', views.order_detail, name='order-detail'),
]
