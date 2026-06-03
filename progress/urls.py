from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='progress'),
    path('create/', views.create_record, name='create-progress'),
    path('edit/<int:pk>/', views.edit_record, name='edit-progress'),
    path('delete/<int:pk>/', views.delete_record, name='delete-progress'),
]
