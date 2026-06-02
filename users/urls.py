from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('records/', views.exercise_records, name='exercise-records'),
    path('purchases/', views.purchase_history, name='purchase-history'),
    path('nutrition/', views.nutrition_calculator, name='nutrition-calculator'),
    path('nutrition/tracker/', views.nutrition_tracker, name='nutrition-tracker'),
    path('nutrition/budget-meals/', views.budget_meals, name='budget-meals'),
]