from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core import throttle

from .models import MONEY, CartItem, Order, OrderItem, Plan


def _owned_plan_ids(user):
    return set(OrderItem.objects.filter(order__owner=user).values_list('plan_id', flat=True))


@login_required
def plans(request):
    kind = request.GET.get('kind', '')
    qs = Plan.objects.filter(is_active=True)
    if kind in ('workout', 'diet'):
        qs = qs.filter(kind=kind)
    else:
        kind = ''
    return render(request, 'shop/plans.html', {
        'plans': qs, 'kind': kind, 'owned': _owned_plan_ids(request.user),
        'in_cart': set(CartItem.objects.filter(owner=request.user).values_list('plan_id', flat=True))})


@login_required
def plan_detail(request, slug):
    plan = get_object_or_404(Plan, slug=slug, is_active=True)
    owned = plan.pk in _owned_plan_ids(request.user)
    return render(request, 'shop/plan_detail.html', {
        'plan': plan, 'owned': owned,
        'in_cart': CartItem.objects.filter(owner=request.user, plan=plan).exists()})


@login_required
def my_plans(request):
    items = (OrderItem.objects.filter(order__owner=request.user).select_related('plan', 'order')
             .order_by('-order__created_at'))
    seen, rows = set(), []
    for item in items:
        if item.plan_id not in seen:
            seen.add(item.plan_id)
            rows.append(item)
    return render(request, 'shop/my_plans.html', {'rows': rows})


def _cart(user):
    items = list(CartItem.objects.filter(owner=user, plan__is_active=True).select_related('plan'))
    total = sum((i.plan.price for i in items), Decimal('0')).quantize(MONEY)
    return items, total


@login_required
def cart(request):
    items, total = _cart(request.user)
    return render(request, 'shop/cart.html', {'items': items, 'total': total})


@login_required
@require_POST
def cart_add(request, slug):
    plan = get_object_or_404(Plan, slug=slug, is_active=True)
    if plan.pk in _owned_plan_ids(request.user):
        messages.info(request, 'You already own this plan.')
        return redirect('shop:plan-detail', slug=plan.slug)
    CartItem.objects.get_or_create(owner=request.user, plan=plan)
    messages.success(request, f'Added "{plan.title}" to your cart.')
    return redirect('shop:cart')


@login_required
@require_POST
def cart_remove(request, slug):
    CartItem.objects.filter(owner=request.user, plan__slug=slug).delete()
    return redirect('shop:cart')


@login_required
@require_POST
def checkout(request):
    key = throttle.make_key('checkout', request.user.pk)
    if throttle.exceeded(key, settings.CHECKOUT_MAX_PER_HOUR, 3600):
        response = HttpResponse('Too many checkouts. Please try again later.', status=429, content_type='text/plain')
        response['Retry-After'] = '3600'
        return response
    with transaction.atomic():
        owned = _owned_plan_ids(request.user)
        # Prices always come from the database. The form sends nothing but the button press.
        items = [i for i in CartItem.objects.select_for_update().filter(owner=request.user, plan__is_active=True)
                 .select_related('plan') if i.plan_id not in owned]
        if not items:
            messages.error(request, 'Your cart is empty.')
            return redirect('shop:cart')
        total = sum((i.plan.price for i in items), Decimal('0')).quantize(MONEY)
        order = Order.objects.create(owner=request.user, total=total)
        OrderItem.objects.bulk_create([OrderItem(order=order, plan=i.plan, title=i.plan.title, price=i.plan.price) for i in items])
        CartItem.objects.filter(owner=request.user).delete()
    messages.success(request, f'Order {order.reference} complete. This is a demo checkout, so no payment was taken.')
    return redirect('shop:order-detail', reference=order.reference)


@login_required
def orders(request):
    return render(request, 'shop/orders.html', {'orders': Order.objects.filter(owner=request.user).prefetch_related('items')})


@login_required
def order_detail(request, reference):
    order = get_object_or_404(Order.objects.filter(owner=request.user).prefetch_related('items__plan'), reference=reference)
    return render(request, 'shop/order_detail.html', {'order': order})
