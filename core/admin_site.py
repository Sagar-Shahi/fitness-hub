from django.conf import settings
from django.contrib import admin
from django.http import HttpResponse

from . import throttle


class ThrottledAdminSite(admin.AdminSite):
    """The Django admin, with the same login lockout as the main site.

    After LOGIN_MAX_FAILURES wrong attempts from one address, further attempts are refused for
    LOGIN_LOCKOUT_SECONDS, even with the right password.
    """

    def login(self, request, extra_context=None):
        if request.method != 'POST':
            return super().login(request, extra_context)

        key = throttle.make_key('admin-login-fail', throttle.client_ip(request))
        if throttle.count(key) >= settings.LOGIN_MAX_FAILURES:
            response = HttpResponse(
                'Too many failed login attempts. Please wait a few minutes and try again.',
                status=429,
                content_type='text/plain; charset=utf-8',
            )
            response['Retry-After'] = str(settings.LOGIN_LOCKOUT_SECONDS)
            return response

        response = super().login(request, extra_context)
        if response.status_code == 200:  # the login form was shown again: the attempt failed
            throttle.hit(key, settings.LOGIN_LOCKOUT_SECONDS)
        else:
            throttle.reset(key)
        return response
