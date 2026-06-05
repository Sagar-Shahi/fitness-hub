from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('about/', views.about, name='about'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit-profile'),
    path('profile/goal/', views.select_goal, name='select-goal'),
    path('records/', views.exercise_records, name='exercise-records'),
    path('settings/', views.settings_hub, name='settings-hub'),
    path('settings/account/', views.settings_account, name='settings-account'),
    path('settings/password/', views.settings_password, name='settings-password'),
]
