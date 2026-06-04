from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg, Count
from django.core.paginator import Paginator

from .models import Category, Product, Order, OrderItem
from .cart_utils import get_or_create_cart
from .forms import CheckoutForm


SORT_CHOICES = {
    'newest': '-created_at',
    'price_low': 'price',
    'price_high': '-price',
    'rating': '-rating',
    'name': 'name',
}


def store_home(request):
    categories = Category.objects.filter(is_active=True)
    featured = (
        Product.objects.filter(is_active=True, is_featured=True)
        .select_related('category')[:8]
    )
    latest = (
        Product.objects.filter(is_active=True)
        .select_related('category')[:8]
    )
    top_rated = (
        Product.objects.filter(is_active=True, rating__gte=4.0)
        .order_by('-rating')[:4]
    )
    return render(request, 'store/store_home.html', {
        'categories': categories,
        'featured': featured,
        'latest': latest,
        'top_rated': top_rated,
    })


def product_list(request, category_slug=None):
    category = None
    qs = Product.objects.filter(is_active=True).select_related('category')

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug, is_active=True)
        qs = qs.filter(category=category)

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(name__icontains=search) |
            Q(short_description__icontains=search) |
            Q(brand__icontains=search) |
            Q(category__name__icontains=search)
        )

    sort = request.GET.get('sort', 'newest')
    if sort in SORT_CHOICES:
        qs = qs.order_by(SORT_CHOICES[sort])

    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        try:
            qs = qs.filter(price__gte=float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            qs = qs.filter(price__lte=float(max_price))
        except ValueError:
            pass

    paginator = Paginator(qs, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    categories = Category.objects.filter(is_active=True)
    return render(request, 'store/product_list.html', {
        'category': category,
        'categories': categories,
        'products': page_obj.object_list,
        'page_obj': page_obj,
        'search': search,
        'sort': sort,
        'min_price': min_price or '',
        'max_price': max_price or '',
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    related = (
        Product.objects
        .filter(category=product.category, is_active=True)
        .exclude(pk=product.pk)[:4]
    )
    return render(request, 'store/product_detail.html', {
        'product': product,
        'related': related,
    })


def add_to_cart(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    cart = get_or_create_cart(request)
    try:
        quantity = max(1, int(request.POST.get('quantity', 1)))
    except (TypeError, ValueError):
        quantity = 1

    item, created = cart.items.get_or_create(
        product=product, defaults={'quantity': quantity}
    )
    if not created:
        item.quantity += quantity
        item.save()

    messages.success(request, f'Added {product.name} to your cart.')
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'ok': True, 'count': cart.item_count()})
    return redirect('view-cart')


def view_cart(request):
    cart = get_or_create_cart(request)
    return render(request, 'store/cart.html', {'cart': cart})


def update_cart(request, item_id):
    cart = get_or_create_cart(request)
    item = get_object_or_404(cart.items, pk=item_id)
    try:
        quantity = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        quantity = 1

    if quantity <= 0:
        item.delete()
        messages.info(request, f'Removed {item.product.name} from your cart.')
    else:
        item.quantity = quantity
        item.save()
        messages.success(request, f'Updated {item.product.name} quantity.')
    return redirect('view-cart')


def remove_from_cart(request, item_id):
    cart = get_or_create_cart(request)
    item = get_object_or_404(cart.items, pk=item_id)
    name = item.product.name
    item.delete()
    messages.info(request, f'Removed {name} from your cart.')
    return redirect('view-cart')


@login_required
def checkout(request):
    cart = get_or_create_cart(request)
    if cart.is_empty():
        messages.warning(request, 'Your cart is empty.')
        return redirect('view-cart')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.subtotal = cart.subtotal()
            order.shipping_cost = cart.shipping()
            order.tax = cart.tax()
            order.total = cart.total()
            order.save()

            for item in cart.items.select_related('product'):
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    product_name=item.product.name,
                    product_price=item.product.price,
                    quantity=item.quantity,
                )
                item.product.stock = max(0, item.product.stock - item.quantity)
                item.product.save()

            cart.items.all().delete()
            messages.success(request, f'Order {order.order_number} placed successfully!')
            return redirect('order-detail', order_number=order.order_number)
    else:
        form = CheckoutForm()

    return render(request, 'store/checkout.html', {
        'cart': cart,
        'form': form,
    })


@login_required
def order_history(request):
    orders = (
        Order.objects
        .filter(user=request.user)
        .prefetch_related('items')
        .order_by('-created_at')
    )
    return render(request, 'store/orders.html', {'orders': orders})


@login_required
def order_detail(request, order_number):
    order = get_object_or_404(
        Order, order_number=order_number, user=request.user,
    )
    return render(request, 'store/order_detail.html', {'order': order})
