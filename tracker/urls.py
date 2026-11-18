from django.urls import path

from . import views
from .progress import progress
from .library import exercise_library

app_name = 'tracker'

urlpatterns = [
    path('app/', views.dashboard, name='dashboard'),
    path('app/progress/', progress, name='progress'),
    path('app/exercise-library/', exercise_library, name='exercise-library'),
    path('app/goals/', views.goals, name='goals'),
    path('app/workouts/', views.workout_list, name='workout-list'),
    path('app/workouts/new/', views.workout_create, name='workout-create'),
    path('app/workouts/export.csv', views.export_csv, name='export'),
    path('app/workouts/<int:pk>/', views.workout_detail, name='workout-detail'),
    path('app/exercises/<int:exercise_pk>/tutorials/', views.exercise_tutorials, name='exercise-tutorials'),
    path('app/workouts/<int:pk>/edit/', views.workout_edit, name='workout-edit'),
    path('app/workouts/<int:pk>/delete/', views.workout_delete, name='workout-delete'),
    path('app/workouts/<int:pk>/exercises/add/', views.exercise_add, name='exercise-add'),
    path('app/workouts/<int:pk>/exercises/<int:exercise_pk>/delete/', views.exercise_delete, name='exercise-delete'),
    path('app/workouts/<int:pk>/exercises/<int:exercise_pk>/sets/add/', views.exercise_set_add, name='exercise-set-add'),
    path('app/workouts/<int:pk>/exercises/<int:exercise_pk>/sets/<int:set_pk>/edit/', views.exercise_set_edit, name='exercise-set-edit'),
    path('app/workouts/<int:pk>/exercises/<int:exercise_pk>/sets/<int:set_pk>/delete/', views.exercise_set_delete, name='exercise-set-delete'),
    path('app/weight/', views.weight, name='weight'),
    path('app/weight/<int:pk>/delete/', views.weight_delete, name='weight-delete'),
    path('app/meals/', views.meals, name='meals'),
    path('app/meals/<int:pk>/delete/', views.meal_delete, name='meal-delete'),
]
