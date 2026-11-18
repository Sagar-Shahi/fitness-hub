from django.conf import settings

# External audio is permitted only through media-src. Scripts, styles, images and API calls remain same-origin.
CSP = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self'; "
    "img-src 'self' data: https://i.ytimg.com; "
    "font-src 'self'; "
    "connect-src 'self'; "
    "media-src 'self' https: blob: data:; "
    "frame-src 'self' https://www.youtube-nocookie.com https://www.youtube.com; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "frame-ancestors 'none'"
)
ADMIN_CSP = CSP.replace("style-src 'self'", "style-src 'self' 'unsafe-inline'")

PERMISSIONS_POLICY = 'camera=(), microphone=(), geolocation=(), payment=(), usb=(), interest-cohort=()'


class SecurityHeadersMiddleware:
    """Adds a Content-Security-Policy, a Permissions-Policy and no-store caching."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        is_admin = request.path.startswith('/' + settings.ADMIN_URL)
        response.headers.setdefault('Content-Security-Policy', ADMIN_CSP if is_admin else CSP)
        response.headers.setdefault('Permissions-Policy', PERMISSIONS_POLICY)
        response.headers.setdefault('Cache-Control', 'no-store')
        return response
