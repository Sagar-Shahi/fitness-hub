"""Small rate limiter built on Django's cache, plus a safe way to find the visitor's address.

The default cache lives inside one server process, which is fine for a small single-process
deployment. With several workers, point CACHES at Redis or Memcached and nothing else changes.
"""
import hashlib
import ipaddress

from django.conf import settings
from django.core.cache import cache


def client_ip(request):
    """The visitor's IP address.

    Without a trusted proxy only REMOTE_ADDR is used, because X-Forwarded-For can be forged by
    the visitor. With DJANGO_TRUSTED_PROXY_COUNT=N, the address is the N-th entry from the right
    of X-Forwarded-For, which is the one added by your own outermost proxy.
    """
    remote = request.META.get('REMOTE_ADDR', '')
    proxies = settings.TRUSTED_PROXY_COUNT
    if proxies > 0:
        parts = [p.strip() for p in request.META.get('HTTP_X_FORWARDED_FOR', '').split(',') if p.strip()]
        if len(parts) >= proxies:
            try:
                return str(ipaddress.ip_address(parts[-proxies]))
            except ValueError:
                pass
    return remote or 'unknown'


def make_key(prefix, *parts):
    """A cache key of fixed length, so long or odd usernames can never break the cache backend."""
    digest = hashlib.sha256('|'.join(str(p) for p in parts).encode('utf-8')).hexdigest()[:32]
    return f'fh:{prefix}:{digest}'


def hit(key, window_seconds):
    """Count one event for `key` inside a window and return the new count."""
    if cache.add(key, 1, window_seconds):
        return 1
    try:
        return cache.incr(key)
    except ValueError:  # the key expired between add() and incr()
        cache.set(key, 1, window_seconds)
        return 1


def count(key):
    return cache.get(key, 0)


def reset(key):
    cache.delete(key)


def exceeded(key, limit, window_seconds):
    """Count this event, and say whether it went over `limit` inside the window."""
    return hit(key, window_seconds) > limit
