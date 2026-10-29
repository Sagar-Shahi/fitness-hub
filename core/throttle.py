"""Tiny cache-backed rate limiter (no third-party packages needed).

Counts hits per (scope, identifier) inside a fixed time window. Django's default
local-memory cache is per process, which is fine for a single-server deployment.
If you run several processes or servers, point CACHES at a shared backend
(Redis, Memcached or the database cache) so the counts are shared.
"""

import hashlib

from django.core.cache import cache


def client_ip(request) -> str:
    """Return the peer address.

    X-Forwarded-For is deliberately ignored because clients can forge it. If the
    app sits behind a trusted reverse proxy, configure the proxy to set
    REMOTE_ADDR (or add a vetted middleware) instead of trusting the header here.
    """
    return request.META.get('REMOTE_ADDR') or 'unknown'


def _key(scope: str, ident: str) -> str:
    digest = hashlib.sha256(ident.lower().encode('utf-8')).hexdigest()[:32]
    return f'throttle:{scope}:{digest}'


def is_limited(scope: str, ident: str, limit: int) -> bool:
    """True when `ident` has already used up `limit` hits in the current window."""
    return cache.get(_key(scope, ident), 0) >= limit


def hit(scope: str, ident: str, window_seconds: int) -> int:
    """Record one hit and return the new count. The window starts at the first hit."""
    key = _key(scope, ident)
    if cache.add(key, 1, window_seconds):
        return 1
    try:
        return cache.incr(key)
    except ValueError:  # key expired between add() and incr()
        cache.set(key, 1, window_seconds)
        return 1


def reset(scope: str, ident: str) -> None:
    cache.delete(_key(scope, ident))
