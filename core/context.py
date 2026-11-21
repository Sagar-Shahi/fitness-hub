from django.conf import settings


def auth_options(request):
    """Lets templates show the Google button only when Google sign-in is configured."""
    return {'google_auth_enabled': settings.GOOGLE_AUTH_ENABLED}
