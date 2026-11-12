import hashlib
import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone

KEY_PREFIX = 'fh_'


def hash_key(raw_key):
    """API keys are long random values, so a plain SHA-256 is enough. Only the hash is stored."""
    return hashlib.sha256(raw_key.encode('utf-8')).hexdigest()


class ApiKey(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='api_keys')
    name = models.CharField(max_length=60)
    prefix = models.CharField(max_length=12, editable=False)  # shown in the list, so keys can be told apart
    key_hash = models.CharField(max_length=64, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.prefix}...)'

    @property
    def is_active(self):
        return self.revoked_at is None

    def revoke(self):
        self.revoked_at = timezone.now()
        self.save(update_fields=['revoked_at'])

    @classmethod
    def issue(cls, owner, name):
        """Create a key. Returns (ApiKey, raw_key). The raw key exists only in this return value."""
        raw_key = KEY_PREFIX + secrets.token_urlsafe(32)
        key = cls.objects.create(owner=owner, name=name, prefix=raw_key[:10], key_hash=hash_key(raw_key))
        return key, raw_key
