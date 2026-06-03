from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='progress'),
    path('log/<slug:slug>/', views.log_exercise, name='log-exercise'),
]
