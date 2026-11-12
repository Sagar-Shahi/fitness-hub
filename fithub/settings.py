"""Django settings for FitHub.

Security defaults:
- Debug mode is OFF unless DJANGO_DEBUG=True is set (for example by a local .env file).
- Outside debug mode the app refuses to start without DJANGO_SECRET_KEY and DJANGO_ALLOWED_HOSTS.
- Outside debug mode cookies are secure, HTTPS is forced and HSTS is sent.
"""
import os
import sys
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

try:  # python-dotenv is optional: real environment variables always win over .env
    from dotenv import load_dotenv

    load_dotenv(BASE_DIR / '.env')
except ImportError:  # pragma: no cover
    pass


def env_bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in {'1', 'true', 'yes', 'on'}


def env_int(name, default):
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def env_list(name):
    return [item.strip() for item in os.environ.get(name, '').split(',') if item.strip()]


DEBUG = env_bool('DJANGO_DEBUG', False)
RUNNING_TESTS = len(sys.argv) > 1 and sys.argv[1] == 'test'
PRODUCTION = not DEBUG and not RUNNING_TESTS

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', '')
if not SECRET_KEY:
    if PRODUCTION:
        raise ImproperlyConfigured(
            'Set DJANGO_SECRET_KEY (see .env.example). For local development copy .env.example '
            'to .env, which also sets DJANGO_DEBUG=True.'
        )
    # Development and tests only. This is not a secret, so never rely on it for a live site.
    SECRET_KEY = 'insecure-development-key-set-DJANGO_SECRET_KEY-for-real-use'  # nosec B105

ALLOWED_HOSTS = env_list('DJANGO_ALLOWED_HOSTS')
if DEBUG and not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']
if PRODUCTION and not ALLOWED_HOSTS:
    raise ImproperlyConfigured('Set DJANGO_ALLOWED_HOSTS to your domain, for example fit.example.com.')

# The admin lives at a path you choose. Change it in production, and keep it out of public docs.
ADMIN_URL = os.environ.get('DJANGO_ADMIN_URL', 'admin-console/').strip('/') + '/'

INSTALLED_APPS = [
    'core.admin_config.FitHubAdminConfig',  # django.contrib.admin with login rate limiting
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'core',
    'accounts',
    'tracker',
    'shop',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'core.middleware.SecurityHeadersMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'fithub.urls'
WSGI_APPLICATION = 'fithub.wsgi.application'
ASGI_APPLICATION = 'fithub.asgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'shop.context.cart',
            ],
        },
    },
]

DATABASES = {
    'default': dj_database_url.config(
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}',
        conn_max_age=60,
    )
}
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Passwords -------------------------------------------------------------------------------
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',  # keeps old hashes working
]
if RUNNING_TESTS:  # a fast hasher keeps the test suite quick; never used outside tests
    PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 10}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'tracker:dashboard'
LOGOUT_REDIRECT_URL = 'home'

# --- Internationalisation ----------------------------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = os.environ.get('DJANGO_TIME_ZONE', 'UTC')
USE_I18N = True
USE_TZ = True

# --- Static files (served by WhiteNoise, so no separate web server is needed) --------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage'},
}

# --- Sessions, cookies and request limits ------------------------------------------------------
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = True  # no script on the site reads the token, so hide it from scripts
CSRF_COOKIE_SAMESITE = 'Lax'
DATA_UPLOAD_MAX_MEMORY_SIZE = 262_144  # 256 KB; the site has no uploads
FILE_UPLOAD_MAX_MEMORY_SIZE = 262_144
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'

# --- Reverse proxies (Render, Railway, nginx, Cloudflare ...) ------------------------------------
# How many trusted proxies sit in front of the app. 0 means visitors connect directly.
# With a value above 0 the visitor's address is read from X-Forwarded-For (counting from the right),
# and X-Forwarded-Proto is trusted to detect HTTPS. Only set it to the number you really have.
TRUSTED_PROXY_COUNT = env_int('DJANGO_TRUSTED_PROXY_COUNT', 0)
if TRUSTED_PROXY_COUNT > 0:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# --- Rate limits and quotas ------------------------------------------------------------------
LOGIN_MAX_FAILURES = env_int('LOGIN_MAX_FAILURES', 5)
LOGIN_LOCKOUT_SECONDS = env_int('LOGIN_LOCKOUT_SECONDS', 300)
REGISTER_MAX_PER_HOUR = env_int('REGISTER_MAX_PER_HOUR', 10)
API_RATE_USER = os.environ.get('API_RATE_USER', '120/min')
API_RATE_ANON = os.environ.get('API_RATE_ANON', '20/min')
API_KEY_FAILURES_PER_5_MIN = env_int('API_KEY_FAILURES_PER_5_MIN', 20)
MAX_WORKOUTS_PER_USER = env_int('MAX_WORKOUTS_PER_USER', 5000)
MAX_EXERCISES_PER_WORKOUT = env_int('MAX_EXERCISES_PER_WORKOUT', 40)
MAX_MEALS_PER_DAY = env_int('MAX_MEALS_PER_DAY', 20)
CHECKOUT_MAX_PER_HOUR = env_int('CHECKOUT_MAX_PER_HOUR', 10)
MAX_API_KEYS_PER_USER = env_int('MAX_API_KEYS_PER_USER', 5)

# --- REST API --------------------------------------------------------------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'accounts.api_auth.ApiKeyAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # enforces CSRF for browser use
    ],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],  # no browsable HTML API
    'DEFAULT_PARSER_CLASSES': ['rest_framework.parsers.JSONParser'],
    'DEFAULT_THROTTLE_CLASSES': ['core.api_throttles.UserBurstThrottle', 'core.api_throttles.AnonBurstThrottle'],
    'DEFAULT_PAGINATION_CLASS': 'tracker.pagination.StandardPagination',
    'PAGE_SIZE': 20,
    'NUM_PROXIES': TRUSTED_PROXY_COUNT,
    'UNAUTHENTICATED_USER': None,
}

# --- Logging ---------------------------------------------------------------------------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': os.environ.get('DJANGO_LOG_LEVEL', 'INFO')},
}

# --- Production security ---------------------------------------------------------------------
# Switched on whenever DJANGO_DEBUG is not True. Verify with: python manage.py check --deploy
if PRODUCTION:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = env_bool('DJANGO_SECURE_SSL_REDIRECT', True)
    SECURE_REDIRECT_EXEMPT = [r'^healthz/$']  # so a load balancer can probe over plain HTTP
    # Start small. Raise DJANGO_HSTS_SECONDS to 31536000 (one year) once HTTPS works everywhere.
    SECURE_HSTS_SECONDS = env_int('DJANGO_HSTS_SECONDS', 3600)
    # Only switch these on when every subdomain of your domain is served over HTTPS.
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool('DJANGO_HSTS_INCLUDE_SUBDOMAINS', False)
    SECURE_HSTS_PRELOAD = env_bool('DJANGO_HSTS_PRELOAD', False)
    CSRF_TRUSTED_ORIGINS = env_list('DJANGO_CSRF_TRUSTED_ORIGINS')
