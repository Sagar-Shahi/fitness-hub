from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from core import throttle

from .forms import ApiKeyForm, CaseInsensitiveAuthenticationForm, RegisterForm
from .models import ApiKey


class ThrottledLoginView(LoginView):
    """Case-insensitive login that slows down password guessing.

    After LOGIN_MAX_FAILURES wrong attempts for the same username from the same address, more attempts
    are refused for LOGIN_LOCKOUT_SECONDS, even if the password is then correct.
    """

    template_name = 'accounts/login.html'
    authentication_form = CaseInsensitiveAuthenticationForm
    redirect_authenticated_user = True

    def _failure_key(self):
        username = (self.request.POST.get('username') or '').strip().lower()
        return throttle.make_key('login-fail', throttle.client_ip(self.request), username)

    def post(self, request, *args, **kwargs):
        if throttle.count(self._failure_key()) >= settings.LOGIN_MAX_FAILURES:
            form = self.authentication_form(request=request, data=request.POST, locked=True)
            return self.render_to_response(self.get_context_data(form=form), status=429)
        return super().post(request, *args, **kwargs)

    def form_invalid(self, form):
        throttle.hit(self._failure_key(), settings.LOGIN_LOCKOUT_SECONDS)
        return super().form_invalid(form)

    def form_valid(self, form):
        throttle.reset(self._failure_key())
        return super().form_valid(form)


def register(request):
    if request.user.is_authenticated:
        return redirect('tracker:dashboard')

    if request.method == 'POST':
        key = throttle.make_key('register', throttle.client_ip(request))
        if throttle.exceeded(key, settings.REGISTER_MAX_PER_HOUR, 3600):
            response = HttpResponse('Too many sign-up attempts. Please try again later.', status=429, content_type='text/plain')
            response['Retry-After'] = '3600'
            return response
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Welcome to FitHub. Set your goals to personalise your dashboard.')
            return redirect('tracker:goals')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


class PasswordChange(PasswordChangeView):
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('accounts:password-change')

    def form_valid(self, form):
        messages.success(self.request, 'Your password was changed.')
        return super().form_valid(form)


@login_required
def api_keys(request):
    return render(request, 'accounts/api_keys.html', {
        'keys': request.user.api_keys.all(),
        'form': ApiKeyForm(),
        'max_keys': settings.MAX_API_KEYS_PER_USER,
    })


@login_required
@require_POST
def api_key_create(request):
    form = ApiKeyForm(request.POST)
    active = request.user.api_keys.filter(revoked_at__isnull=True).count()
    if active >= settings.MAX_API_KEYS_PER_USER:
        messages.error(request, f'You can have up to {settings.MAX_API_KEYS_PER_USER} active keys. Revoke one first.')
        return redirect('accounts:api-keys')
    if not form.is_valid():
        return render(request, 'accounts/api_keys.html', {
            'keys': request.user.api_keys.all(), 'form': form, 'max_keys': settings.MAX_API_KEYS_PER_USER,
        }, status=400)

    _key, raw_key = ApiKey.issue(request.user, form.cleaned_data['name'])
    # The key is shown in this response only and is never stored, so it cannot be shown again.
    # It is rendered directly instead of redirecting, because messages can be kept in a cookie.
    return render(request, 'accounts/api_keys.html', {
        'keys': request.user.api_keys.all(), 'form': ApiKeyForm(), 'new_key': raw_key,
        'max_keys': settings.MAX_API_KEYS_PER_USER,
    })


@login_required
@require_POST
def api_key_revoke(request, pk):
    key = get_object_or_404(ApiKey, pk=pk, owner=request.user)
    if key.is_active:
        key.revoke()
        messages.success(request, f'The key "{key.name}" was revoked. It no longer works.')
    return redirect('accounts:api-keys')
