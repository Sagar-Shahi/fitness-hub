from django.urls import path
from . import views

urlpatterns = [
    path('', views.inspiration_feed, name='inspiration-feed'),
]