import logging

from .models import CartItem

logger = logging.getLogger(__name__)


def cart(request):
    """Cart size for the menu. Must never break a page: error pages run it with no user, or with the database down."""
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return {}
    try:
        return {'cart_count': CartItem.objects.filter(owner=user).count()}
    except Exception:  # noqa: BLE001
        logger.exception('Could not count cart items')
        return {}
