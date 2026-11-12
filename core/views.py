import logging

from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_safe

logger = logging.getLogger(__name__)


@require_safe
def home(request):
    return render(request, 'home.html')


@require_safe
def health(request):
    """Used by hosting platforms to check the app is up. It says nothing about the system itself."""
    try:
        connection.ensure_connection()
    except Exception:  # noqa: BLE001 - any database problem means "not healthy"
        logger.exception('Health check could not reach the database')
        return JsonResponse({'status': 'unavailable'}, status=503)
    return JsonResponse({'status': 'ok'})


def error_400(request, exception=None):
    return render(request, '400.html', status=400)


def error_403(request, exception=None):
    return render(request, '403.html', status=403)


def error_404(request, exception=None):
    return render(request, '404.html', status=404)


def error_500(request):
    return render(request, '500.html', status=500)
