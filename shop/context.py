import logging

from .models import CartItem, OrderItem

logger = logging.getLogger(__name__)


def cart(request):
    """Cart size for the menu. Must never break a page: error pages run it with no user, or with the database down."""
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return {}
    try:
        owned_plan_ids = OrderItem.objects.filter(order__owner=user).values_list('plan_id', flat=True)
        count = CartItem.objects.filter(owner=user, plan__is_active=True).exclude(plan_id__in=owned_plan_ids).count()
        return {'cart_count': count}
    except Exception:  # noqa: BLE001
        logger.exception('Could not count cart items')
        return {}
