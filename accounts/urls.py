from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.ThrottledLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),  # POST only
    path('password/', views.PasswordChange.as_view(), name='password-change'),
    path('api-keys/', views.api_keys, name='api-keys'),
    path('api-keys/new/', views.api_key_create, name='api-key-create'),
    path('api-keys/<int:pk>/revoke/', views.api_key_revoke, name='api-key-revoke'),
]
