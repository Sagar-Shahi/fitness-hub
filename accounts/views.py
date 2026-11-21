from django.conf import settings
from django.contrib import messages
import secrets

from django.contrib.auth import get_user_model, logout, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, PasswordChangeView, PasswordResetView
from django.http import Http404, HttpResponse
from django.utils.http import url_has_allowed_host_and_scheme
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from core import throttle

from .forms import ApiKeyForm, CaseInsensitiveAuthenticationForm, RegisterForm
from . import google_auth
from .models import ApiKey, GoogleIdentity
from tracker.models import BodyMetric, Profile


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


def google_login(request):
    if not settings.GOOGLE_AUTH_ENABLED:
        raise Http404()
    if request.user.is_authenticated:
        return redirect('tracker:dashboard')
    state, nonce = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    request.session['google_state'] = state
    request.session['google_nonce'] = nonce
    next_url = request.GET.get('next', '')
    if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        request.session['google_next'] = next_url
    return redirect(google_auth.authorization_url(request, state, nonce))


def google_callback(request):
    if not settings.GOOGLE_AUTH_ENABLED:
        raise Http404()
    state = request.session.pop('google_state', '')
    nonce = request.session.pop('google_nonce', '')
    next_url = request.session.pop('google_next', '')

    def fail(message):
        messages.error(request, message)
        return redirect('accounts:login')

    key = throttle.make_key('google-callback', throttle.client_ip(request))
    if throttle.exceeded(key, 30, 3600):
        return fail('Too many sign-in attempts. Please try again later.')
    code = request.GET.get('code', '')
    given_state = request.GET.get('state', '')
    if request.GET.get('error') or not code or not state or not secrets.compare_digest(state, given_state):
        return fail('Google sign-in was cancelled or could not be verified. Please try again.')
    try:
        tokens = google_auth.exchange_code(request, code)
        claims = google_auth.read_id_token(tokens.get('id_token', ''), nonce)
    except google_auth.GoogleAuthError as exc:
        return fail(str(exc))

    User = get_user_model()
    identity = GoogleIdentity.objects.select_related('user').filter(subject=claims['sub']).first()
    created = False
    if identity:
        user = identity.user
        if not user.is_active:
            return fail('This account is disabled.')
    else:
        email = claims['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            return fail('An account with that email already exists. Log in with your password instead.')
        user = User(username=google_auth.unique_username(email, claims.get('name', '')), email=email)
        user.set_unusable_password()
        user.save()
        GoogleIdentity.objects.create(user=user, subject=claims['sub'])
        Profile.objects.get_or_create(owner=user)
        created = True
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    if created:
        messages.success(request, 'Welcome to FitHub. Set your goals to personalise your dashboard.')
        return redirect('tracker:goals')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return redirect(next_url)
    return redirect('tracker:dashboard')


class ThrottledPasswordResetView(PasswordResetView):
    """Limit reset-email requests per visitor without revealing whether an email exists."""

    def post(self, request, *args, **kwargs):
        key = throttle.make_key('password-reset', throttle.client_ip(request))
        if throttle.exceeded(key, settings.PASSWORD_RESET_MAX_PER_HOUR, 3600):
            response = HttpResponse(
                'Too many password reset requests. Please try again later.',
                status=429,
                content_type='text/plain',
            )
            response['Retry-After'] = '3600'
            return response
        return super().post(request, *args, **kwargs)


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


@login_required
def delete_account(request):
    """Let a person erase their account and everything in it. The password is asked for again first."""
    if request.method == 'POST':
        key = throttle.make_key('delete-account', request.user.pk)
        if throttle.exceeded(key, 5, 3600):
            return HttpResponse('Too many attempts. Please try again later.', status=429, content_type='text/plain')
        if not request.user.check_password(request.POST.get('password', '')):
            messages.error(request, 'That password is not correct, so nothing was deleted.')
            return render(request, 'accounts/delete_account.html', status=400)
        user = request.user
        logout(request)
        user.delete()  # workouts, meals, weights, orders, cart and API keys are removed with it
        messages.success(request, 'Your account and all of its data were deleted.')
        return redirect('home')
    return render(request, 'accounts/delete_account.html')
