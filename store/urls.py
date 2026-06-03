from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product-list'),
    path('<slug:slug>/', views.product_detail, name='product-detail'),
    path('cart/add/<slug:slug>/', views.add_to_cart, name='add-to-cart'),
    path('cart/', views.view_cart, name='view-cart'),
    path('cart/update/', views.update_cart, name='update-cart'),
    path('cart/remove/<slug:slug>/', views.remove_from_cart, name='remove-from-cart'),
    path('checkout/', views.checkout, name='checkout'),
]