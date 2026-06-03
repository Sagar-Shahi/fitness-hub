
# exercises/urls.py
from django.urls import path
from . import views  # The dot means "from the current folder"

urlpatterns = [
    path('', views.index, name='home'),
    path('exercises/', views.exercise_list, name='exercise-list'),
    path('exercises/<slug:slug>/', views.exercise_detail, name='exercise-detail'),
]