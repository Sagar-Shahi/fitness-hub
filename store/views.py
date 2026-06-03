from django.http import Http404
from django.shortcuts import get_object_or_404, render
from .models import Product


CATEGORY_META = [
    {
        'slug': Product.TYPE_OUTFIT,
        'title': 'Outfit Products',
        'description': 'Fitness apparel and accessories to keep your training comfortable and stylish.',
    },
    {
        'slug': Product.TYPE_EXERCISE,
        'title': 'Exercise Products',
        'description': 'Equipment, tools, and gear designed to support workout performance.',
    },
    {
        'slug': Product.TYPE_NUTRITION,
        'title': 'Nutrition Products',
        'description': 'Food, supplements, and nutrition items for recovery and wellness.',
    },
]

PRODUCT_SEED = [
    {
        'name': 'Performance Training Tee',
        'description': 'Breathable workout shirt built for movement and comfort.',
        'product_type': Product.TYPE_OUTFIT,
        'price': 24.99,
        'image_url': 'https://images.unsplash.com/photo-1599058917213-85f46f0c0f0d?auto=format&fit=crop&w=800&q=80',
    },
    {
        'name': 'Compression Shorts',
        'description': 'Supportive shorts for dynamic exercise and recovery.',
        'product_type': Product.TYPE_OUTFIT,
        'price': 29.99,
        'image_url': 'https://images.unsplash.com/photo-1505552836794-0518852cf2a5?auto=format&fit=crop&w=800&q=80',
    },
    {
        'name': 'Adjustable Kettlebell',
        'description': 'Space-saving, adjustable kettlebell for strength and conditioning.',
        'product_type': Product.TYPE_EXERCISE,
        'price': 69.99,
        'image_url': 'https://images.unsplash.com/photo-1558611848-73f7eb4001e4?auto=format&fit=crop&w=800&q=80',
    },
    {
        'name': 'Yoga Stability Ball',
        'description': 'Durable stability ball for mobility, core, and balance training.',
        'product_type': Product.TYPE_EXERCISE,
        'price': 34.99,
        'image_url': 'https://images.unsplash.com/photo-1517832207067-4db24a2ae47c?auto=format&fit=crop&w=800&q=80',
    },
    {
        'name': 'Protein Smoothie Mix',
        'description': 'Nutritious powder blend for post-workout recovery and energy.',
        'product_type': Product.TYPE_NUTRITION,
        'price': 27.99,
        'image_url': 'https://images.unsplash.com/photo-1526401485004-3606d5c5f900?auto=format&fit=crop&w=800&q=80',
    },
    {
        'name': 'Electrolyte Drink Pack',
        'description': 'Hydration formula for training and daily wellness.',
        'product_type': Product.TYPE_NUTRITION,
        'price': 14.99,
        'image_url': 'https://images.unsplash.com/photo-1556911268-0e0e2fdf2d3f?auto=format&fit=crop&w=800&q=80',
    },
]


def _seed_products():
    for item in PRODUCT_SEED:
        Product.objects.get_or_create(name=item['name'], defaults=item)


def store_home(request):
    _seed_products()
    return render(request, 'store/store_home.html', {'categories': CATEGORY_META})


def product_list(request, product_type):
    if product_type not in dict(Product.TYPE_CHOICES):
        raise Http404('Product type not found.')

    products = Product.objects.filter(product_type=product_type)
    category_title = dict(Product.TYPE_CHOICES).get(product_type, 'Products')
    return render(
        request,
        'store/product_list.html',
        {
            'products': products,
            'category_title': category_title,
            'product_type': product_type,
        },
    )


def product_detail(request, product_type, slug):
    product = get_object_or_404(Product, slug=slug, product_type=product_type)
    return render(request, 'store/product_detail.html', {'product': product})
