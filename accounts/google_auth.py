"""Minimal "Sign in with Google" (OpenID Connect authorization-code flow).

Security notes:
- A random `state` and `nonce` are stored in the session and checked on return.
- The code is exchanged server-to-server over HTTPS with the client secret, so the returned ID token
  comes straight from Google; its issuer, audience, expiry, nonce and verified email are still checked.
- Accounts are matched by Google's stable subject id, never by email alone. If a password account
  already uses the same email, Google sign-in is refused so nobody can take over an account.
"""
import base64
import json
import re
import time
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse

AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
TOKEN_URL = 'https://oauth2.googleapis.com/token'  # nosec B105
ISSUERS = {'https://accounts.google.com', 'accounts.google.com'}


class GoogleAuthError(Exception):
    pass


def redirect_uri(request):
    return settings.GOOGLE_REDIRECT_URI or request.build_absolute_uri(reverse('accounts:google-callback'))


def authorization_url(request, state, nonce):
    return AUTH_URL + '?' + urlencode({
        'client_id': settings.GOOGLE_CLIENT_ID,
        'redirect_uri': redirect_uri(request),
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'nonce': nonce,
        'prompt': 'select_account',
    })


def exchange_code(request, code):
    body = urlencode({
        'code': code,
        'client_id': settings.GOOGLE_CLIENT_ID,
        'client_secret': settings.GOOGLE_CLIENT_SECRET,
        'redirect_uri': redirect_uri(request),
        'grant_type': 'authorization_code',
    }).encode('ascii')
    req = Request(TOKEN_URL, data=body, headers={'Content-Type': 'application/x-www-form-urlencoded'})  # nosec B310
    try:
        with urlopen(req, timeout=10) as response:  # nosec B310 - fixed https URL
            return json.loads(response.read(200_000).decode('utf-8'))
    except (URLError, ValueError, OSError) as exc:
        raise GoogleAuthError('Google did not accept the sign-in.') from exc


def read_id_token(token, nonce):
    """Return the verified claims of an ID token received directly from Google's token endpoint."""
    try:
        payload = token.split('.')[1]
        claims = json.loads(base64.urlsafe_b64decode(payload + '=' * (-len(payload) % 4)))
    except (IndexError, ValueError, AttributeError) as exc:
        raise GoogleAuthError('Invalid sign-in response.') from exc
    if claims.get('iss') not in ISSUERS:
        raise GoogleAuthError('Invalid sign-in issuer.')
    aud = claims.get('aud')
    if aud != settings.GOOGLE_CLIENT_ID and not (isinstance(aud, list) and settings.GOOGLE_CLIENT_ID in aud):
        raise GoogleAuthError('Invalid sign-in audience.')
    if not isinstance(claims.get('exp'), (int, float)) or claims['exp'] < time.time():
        raise GoogleAuthError('The sign-in expired.')
    if not nonce or claims.get('nonce') != nonce:
        raise GoogleAuthError('Invalid sign-in nonce.')
    if not claims.get('sub') or not claims.get('email') or claims.get('email_verified') is not True:
        raise GoogleAuthError('Your Google email address must be verified.')
    return claims


def unique_username(email, name=''):
    User = get_user_model()
    base = re.sub(r'[^a-z0-9]', '', (email.split('@')[0] or name).lower())[:20] or 'athlete'
    candidate, n = base, 1
    while User.objects.filter(username__iexact=candidate).exists():
        n += 1
        candidate = f'{base}{n}'
    return candidate
