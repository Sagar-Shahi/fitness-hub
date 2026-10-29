"""Extra security headers that Django's SecurityMiddleware does not set."""


class SecurityHeadersMiddleware:
    """Adds Permissions-Policy and a conservative Content-Security-Policy.

    The CSP below only restricts framing, <base> and plugins, so it does not
    break the inline scripts and styles the templates currently use. Tighten it
    (script-src / style-src with nonces) once those are moved to static files.
    """

    HEADERS = {
        'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), payment=(), usb=()',
        'Content-Security-Policy': "frame-ancestors 'none'; base-uri 'self'; object-src 'none'",
        'X-Permitted-Cross-Domain-Policies': 'none',
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        for name, value in self.HEADERS.items():
            response.headers.setdefault(name, value)
        return response
