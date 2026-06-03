from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='goals'),
    path('create/', views.create_goal, name='create-goal'),
]
