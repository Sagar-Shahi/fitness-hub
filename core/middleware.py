from django.conf import settings

# No inline scripts or styles anywhere in the site, so the policy can be strict.
CSP = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self'; "
    "img-src 'self' data:; "
    "font-src 'self'; "
    "connect-src 'self'; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "frame-ancestors 'none'"
)
# Django's own admin uses a few inline styles, so only the admin gets 'unsafe-inline' for styles.
ADMIN_CSP = CSP.replace("style-src 'self'", "style-src 'self' 'unsafe-inline'")

PERMISSIONS_POLICY = 'camera=(), microphone=(), geolocation=(), payment=(), usb=(), interest-cohort=()'


class SecurityHeadersMiddleware:
    """Adds a Content-Security-Policy, a Permissions-Policy and no-store caching to every response.

    `no-store` matters twice: private pages are never kept in a shared cache, and short-link
    redirects always reach the server, so every click is counted. Static files are answered by
    WhiteNoise before this middleware, so they keep their own caching headers.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        is_admin = request.path.startswith('/' + settings.ADMIN_URL)
        response.headers.setdefault('Content-Security-Policy', ADMIN_CSP if is_admin else CSP)
        response.headers.setdefault('Permissions-Policy', PERMISSIONS_POLICY)
        response.headers.setdefault('Cache-Control', 'no-store')
        return response
