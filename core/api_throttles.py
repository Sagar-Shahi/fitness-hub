"""API rate limits. Rates are read from settings each time, so they are easy to change and to test."""
from django.conf import settings
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class UserBurstThrottle(UserRateThrottle):
    scope = 'user'

    def get_rate(self):
        return settings.API_RATE_USER


class AnonBurstThrottle(AnonRateThrottle):
    scope = 'anon'

    def get_rate(self):
        return settings.API_RATE_ANON
