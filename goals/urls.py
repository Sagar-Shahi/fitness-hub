from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='goals'),
    path('create/', views.create_goal, name='create-goal'),
    path('edit/<int:pk>/', views.edit_goal, name='edit-goal'),
    path('delete/<int:pk>/', views.delete_goal, name='delete-goal'),
]
