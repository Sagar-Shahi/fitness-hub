from django.contrib.auth.views import LogoutView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.ThrottledLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),  # POST only
    path('password/', views.PasswordChange.as_view(), name='password-change'),
    path('password-reset/', views.ThrottledPasswordResetView.as_view(
        template_name='accounts/password_reset_form.html',
        email_template_name='accounts/password_reset_email.html',
        subject_template_name='accounts/password_reset_subject.txt',
        success_url='/accounts/password-reset/sent/',
    ), name='password-reset'),
    path('password-reset/sent/', PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html',
    ), name='password-reset-done'),
    path('password-reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html',
        success_url='/accounts/password-reset/complete/',
    ), name='password-reset-confirm'),
    path('password-reset/complete/', PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html',
    ), name='password-reset-complete'),
    path('delete/', views.delete_account, name='delete'),
    path('api-keys/', views.api_keys, name='api-keys'),
    path('api-keys/new/', views.api_key_create, name='api-key-create'),
    path('api-keys/<int:pk>/revoke/', views.api_key_revoke, name='api-key-revoke'),
]
