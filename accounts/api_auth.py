from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import authentication, exceptions

from core import throttle

from .models import KEY_PREFIX, ApiKey, hash_key


class ApiKeyAuthentication(authentication.BaseAuthentication):
    """Authorization: Bearer fh_...

    With no Authorization header this does nothing, so browser sessions still work. A wrong key is
    rejected with a generic message, and repeated wrong keys from one address are slowed down.
    """

    keyword = 'Bearer'

    def authenticate_header(self, request):
        return f'{self.keyword} realm="FitHub API"'

    def authenticate(self, request):
        header = authentication.get_authorization_header(request).decode('latin-1').strip()
        if not header:
            return None
        scheme, _, token = header.partition(' ')
        if scheme.lower() != self.keyword.lower():
            return None
        token = token.strip()

        failures_key = throttle.make_key('apikey-fail', throttle.client_ip(request))
        if throttle.count(failures_key) >= settings.API_KEY_FAILURES_PER_5_MIN:
            raise exceptions.Throttled(wait=300)

        key = None
        if token.startswith(KEY_PREFIX) and len(token) <= 100:
            key = (
                ApiKey.objects.select_related('owner')
                .filter(key_hash=hash_key(token), revoked_at__isnull=True, owner__is_active=True)
                .first()
            )
        if key is None:
            throttle.hit(failures_key, 300)
            raise exceptions.AuthenticationFailed('Invalid API key.')

        now = timezone.now()
        if key.last_used_at is None or now - key.last_used_at > timedelta(minutes=1):
            ApiKey.objects.filter(pk=key.pk).update(last_used_at=now)
        return key.owner, key
