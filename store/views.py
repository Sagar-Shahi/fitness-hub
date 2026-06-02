from django.shortcuts import render, get_object_or_404
from .models import Product

PRODUCT_SEED = [
    {
        'name': 'Pro Dumbbell Set',
        'description': 'Adjustable dumbbell set with durable grip and compact storage.',
        'category': 'Equipment',
        'price': 59.99,
        'image_url': 'https://images.unsplash.com/photo-1599058917213-85f46f0c0f0d?auto=format&fit=crop&w=800&q=80',
    },
    {
        'name': 'Whey Protein Powder',
        'description': 'High-quality protein powder for muscle recovery and performance.',
        'category': 'Nutrition',
        'price': 34.99,
        'image_url': 'https://images.unsplash.com/photo-1592210322493-fb4399144adc?auto=format&fit=crop&w=800&q=80',
    },
    {
        'name': 'Resistance Band Kit',
        'description': 'Set of bands for strength training, stretching, and mobility work.',
        'category': 'Accessories',
        'price': 19.99,
        'image_url': 'https://images.unsplash.com/photo-1598526800385-5915f8b1654e?auto=format&fit=crop&w=800&q=80',
    },
    {
        'name': 'Performance Water Bottle',
        'description': 'Insulated bottle to keep your drink cold during every workout.',
        'category': 'Gear',
        'price': 14.99,
        'image_url': 'https://images.unsplash.com/photo-1541698444083-023c97d3f4b6?auto=format&fit=crop&w=800&q=80',
    },
    {
        'name': 'Recovery Protein Bars',
        'description': 'Delicious protein bars made for post-workout recovery and energy.',
        'category': 'Nutrition',
        'price': 24.99,
        'image_url': 'https://images.unsplash.com/photo-1556911268-0e0e2fdf2d3f?auto=format&fit=crop&w=800&q=80',
    },
    {
        'name': 'Yoga Mat',
        'description': 'Premium non-slip yoga mat for stretching, mobility, and floor workouts.',
        'category': 'Accessories',
        'price': 29.99,
        'image_url': 'https://images.unsplash.com/photo-1517832207067-4db24a2ae47c?auto=format&fit=crop&w=800&q=80',
    },
    {
        'name': 'Shake Bottle',
        'description': 'Leak-proof shaker bottle with built-in mixer for smoothies and supplements.',
        'category': 'Gear',
        'price': 12.99,
        'image_url': 'https://images.unsplash.com/photo-1526401485004-3606d5c5f900?auto=format&fit=crop&w=800&q=80',
    },
    {
        'name': 'Fitness Tracker Band',
        'description': 'Lightweight fitness tracker to monitor steps, heart rate, and daily activity.',
        'category': 'Wearables',
        'price': 49.99,
        'image_url': 'https://images.unsplash.com/photo-1512436991641-6745cdb1723f?auto=format&fit=crop&w=800&q=80',
    },
]


def _seed_products():
    for item in PRODUCT_SEED:
        Product.objects.get_or_create(name=item['name'], defaults=item)


def product_list(request):
    _seed_products()
    products = Product.objects.all()
    return render(request, 'store/product_list.html', {'products': products})


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return render(request, 'store/product_detail.html', {'product': product})
