from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='progress'),
    path('log/<slug:slug>/', views.log_exercise, name='log-exercise'),
    path('edit/<int:pk>/', views.edit_completion, name='progress-edit'),
    path('delete/<int:pk>/', views.delete_completion, name='progress-delete'),
]
