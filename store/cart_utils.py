"""Cart helpers that work for both authenticated and guest users."""


def _get_or_create_session(request):
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key


def get_or_create_cart(request):
    from .models import Cart

    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        # Merge any guest cart into the user cart
        session_key = request.session.session_key
        if session_key:
            guest_cart = Cart.objects.filter(session_key=session_key, user__isnull=True).first()
            if guest_cart and guest_cart.pk != cart.pk:
                for item in guest_cart.items.all():
                    existing = cart.items.filter(product=item.product).first()
                    if existing:
                        existing.quantity += item.quantity
                        existing.save()
                    else:
                        item.cart = cart
                        item.save()
                guest_cart.delete()
        return cart

    session_key = _get_or_create_session(request)
    cart, _ = Cart.objects.get_or_create(session_key=session_key, user__isnull=True)
    return cart


def cart_context(request):
    """Context processor: expose cart count to every template."""
    from .models import Cart

    count = 0
    try:
        if request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user).first()
        else:
            session_key = request.session.session_key
            cart = Cart.objects.filter(session_key=session_key, user__isnull=True).first() if session_key else None
        if cart:
            count = cart.item_count()
    except Exception:
        count = 0
    return {'cart_count': count}
