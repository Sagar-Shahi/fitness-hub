from django.urls import path
from . import views

urlpatterns = [
    path('', views.store_home, name='store-home'),
    path('<slug:product_type>/', views.product_list, name='store-product-list'),
    path('<slug:product_type>/<slug:slug>/', views.product_detail, name='store-product-detail'),
]