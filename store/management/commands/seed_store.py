"""Seed the store with categories and products."""
from django.core.management.base import BaseCommand
from store.models import Category, Product


CATEGORIES = [
    {
        'name': 'Outfits',
        'slug': 'outfits',
        'description': 'Performance apparel and accessories to keep you training in style.',
        'icon': '👕',
        'image_url': 'https://images.unsplash.com/photo-1556906781-9a412961c28c?auto=format&fit=crop&w=900&q=80',
        'display_order': 1,
    },
    {
        'name': 'Gear',
        'slug': 'gear',
        'description': 'Equipment and tools engineered to elevate every workout.',
        'icon': '🏋️',
        'image_url': 'https://images.unsplash.com/photo-1517836357463-d25dfeac3438?auto=format&fit=crop&w=900&q=80',
        'display_order': 2,
    },
    {
        'name': 'Supplements',
        'slug': 'supplements',
        'description': 'Premium nutrition to fuel recovery, performance, and wellness.',
        'icon': '💊',
        'image_url': 'https://images.unsplash.com/photo-1593095948071-474c5cc2989d?auto=format&fit=crop&w=900&q=80',
        'display_order': 3,
    },
]


PRODUCTS = [
    # Outfits
    {
        'category': 'outfits',
        'name': 'Performance Training Tee',
        'short_description': 'Breathable, sweat-wicking shirt built for high-intensity training.',
        'description': 'Engineered with moisture-wicking fabric and four-way stretch, this tee moves with you through every rep, run, and recovery. Flatlock seams prevent chafing, and the athletic cut stays tucked or relaxed on demand.',
        'price': 24.99,
        'compare_at_price': 34.99,
        'image_url': 'https://images.unsplash.com/photo-1581655353564-df123a1eb820?auto=format&fit=crop&w=800&q=80',
        'brand': 'Apex',
        'sku': 'AX-TEE-001',
        'stock': 48,
        'rating': 4.7,
        'review_count': 132,
        'is_featured': True,
    },
    {
        'category': 'outfits',
        'name': 'Compression Shorts',
        'short_description': 'Supportive 4-way stretch shorts for dynamic movement.',
        'description': 'Lightweight compression fabric supports muscles while allowing full range of motion. Anti-odor technology and an elastic waistband keep you focused on the workout, not the gear.',
        'price': 29.99,
        'compare_at_price': 39.99,
        'image_url': 'https://images.unsplash.com/photo-1505552836794-0518852cf2a5?auto=format&fit=crop&w=800&q=80',
        'brand': 'Apex',
        'sku': 'AX-SHT-002',
        'stock': 36,
        'rating': 4.5,
        'review_count': 87,
        'is_featured': True,
    },
    {
        'category': 'outfits',
        'name': 'Performance Hoodie',
        'short_description': 'Cozy warmth meets training-ready construction.',
        'description': 'A brushed-fleece interior and athletic cut make this the perfect layer for warm-ups, cool-downs, and rest-day comfort. Drawcord hood and kangaroo pocket for everyday function.',
        'price': 54.99,
        'compare_at_price': None,
        'image_url': 'https://images.unsplash.com/photo-1556821840-3a63f95609a7?auto=format&fit=crop&w=800&q=80',
        'brand': 'Apex',
        'sku': 'AX-HOD-003',
        'stock': 22,
        'rating': 4.8,
        'review_count': 64,
        'is_featured': False,
    },
    {
        'category': 'outfits',
        'name': 'Training Joggers',
        'short_description': 'Tapered joggers with stretch and storage.',
        'description': 'Soft, mid-weight fabric with articulated knees and zip pockets. Designed to move with you on leg days and rest days alike.',
        'price': 44.99,
        'compare_at_price': 59.99,
        'image_url': 'https://images.unsplash.com/photo-1552902889-9301d4cf75fa?auto=format&fit=crop&w=800&q=80',
        'brand': 'Apex',
        'sku': 'AX-JOG-004',
        'stock': 30,
        'rating': 4.6,
        'review_count': 51,
        'is_featured': False,
    },
    # Gear
    {
        'category': 'gear',
        'name': 'Adjustable Kettlebell',
        'short_description': 'Space-saving, 6-in-1 adjustable kettlebell.',
        'description': 'Quick-dial weight selection from 8–40 lbs replaces six traditional kettlebells. Powder-coated cast iron with a wide, flat base for stability during renegade rows and push-ups.',
        'price': 149.99,
        'compare_at_price': 199.99,
        'image_url': 'https://images.unsplash.com/photo-1517344884509-a0c97ec11bcc?auto=format&fit=crop&w=800&q=80',
        'brand': 'IronCore',
        'sku': 'IR-KBL-101',
        'stock': 18,
        'rating': 4.9,
        'review_count': 211,
        'is_featured': True,
    },
    {
        'category': 'gear',
        'name': 'Yoga Stability Ball',
        'short_description': 'Anti-burst stability ball with pump included.',
        'description': '65 cm professional-grade ball rated to 2,200 lbs. Anti-slip texture and slow-deflate safety design. Includes hand pump and workout guide.',
        'price': 34.99,
        'compare_at_price': None,
        'image_url': 'https://images.unsplash.com/photo-1517832207067-4db24a2ae47c?auto=format&fit=crop&w=800&q=80',
        'brand': 'IronCore',
        'sku': 'IR-BAL-102',
        'stock': 40,
        'rating': 4.4,
        'review_count': 76,
        'is_featured': False,
    },
    {
        'category': 'gear',
        'name': 'Resistance Band Set',
        'short_description': '5-band loop set for strength, mobility, and rehab.',
        'description': 'Five color-coded resistance levels (10–50 lbs) with door anchor, handles, and ankle straps. Compact, travel-ready, and built to last.',
        'price': 29.99,
        'compare_at_price': 44.99,
        'image_url': 'https://images.unsplash.com/photo-1598289431512-b97b0917affc?auto=format&fit=crop&w=800&q=80',
        'brand': 'IronCore',
        'sku': 'IR-BND-103',
        'stock': 60,
        'rating': 4.7,
        'review_count': 158,
        'is_featured': True,
    },
    {
        'category': 'gear',
        'name': 'Lifting Gloves',
        'short_description': 'Padded, breathable gloves for heavy lifts.',
        'description': 'Full palm protection with wrist support strap and breathable mesh back. Silicone grip pattern prevents slipping through deadlifts and pull-ups.',
        'price': 19.99,
        'compare_at_price': None,
        'image_url': 'https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?auto=format&fit=crop&w=800&q=80',
        'brand': 'IronCore',
        'sku': 'IR-GLV-104',
        'stock': 75,
        'rating': 4.3,
        'review_count': 92,
        'is_featured': False,
    },
    # Supplements
    {
        'category': 'supplements',
        'name': 'Whey Protein Isolate',
        'short_description': '25g protein per serving. Low sugar, great taste.',
        'description': 'Premium whey isolate sourced from grass-fed cows. Cold-processed to preserve amino acid integrity. Mixes smoothly in water or milk. Available in chocolate, vanilla, and strawberry.',
        'price': 49.99,
        'compare_at_price': 59.99,
        'image_url': 'https://images.unsplash.com/photo-1593095948071-474c5cc2989d?auto=format&fit=crop&w=800&q=80',
        'brand': 'NutraPro',
        'sku': 'NP-WPI-201',
        'stock': 95,
        'rating': 4.8,
        'review_count': 320,
        'is_featured': True,
    },
    {
        'category': 'supplements',
        'name': 'Pre-Workout Energy',
        'short_description': 'Caffeine, beta-alanine, and citrulline for energy and pumps.',
        'description': '200 mg natural caffeine, 3.2 g beta-alanine, 6 g L-citrulline malate, and 1.5 g creatine monohydrate. No crash, no jitters. 30 servings per container.',
        'price': 39.99,
        'compare_at_price': None,
        'image_url': 'https://images.unsplash.com/photo-1556909211-d5b4d50d3f74?auto=format&fit=crop&w=800&q=80',
        'brand': 'NutraPro',
        'sku': 'NP-PRE-202',
        'stock': 70,
        'rating': 4.6,
        'review_count': 184,
        'is_featured': True,
    },
    {
        'category': 'supplements',
        'name': 'Electrolyte Hydration',
        'short_description': 'Sugar-free electrolyte mix with key minerals.',
        'description': '1,000 mg sodium, 200 mg potassium, 60 mg magnesium per serving. No sugar, no artificial colors. 30 stick packs—perfect for training, travel, and hot workouts.',
        'price': 24.99,
        'compare_at_price': 29.99,
        'image_url': 'https://images.unsplash.com/photo-1556911268-0e0e2fdf2d3f?auto=format&fit=crop&w=800&q=80',
        'brand': 'NutraPro',
        'sku': 'NP-ELE-203',
        'stock': 120,
        'rating': 4.7,
        'review_count': 142,
        'is_featured': False,
    },
    {
        'category': 'supplements',
        'name': 'Plant Protein Blend',
        'short_description': 'Pea, rice, and hemp protein for vegan recovery.',
        'description': '24 g complete amino acid profile from a blend of pea, brown rice, and hemp proteins. Smooth texture, easy on digestion. Naturally flavored with cocoa and stevia.',
        'price': 44.99,
        'compare_at_price': None,
        'image_url': 'https://images.unsplash.com/photo-1622485830941-c0e88dacd0a4?auto=format&fit=crop&w=800&q=80',
        'brand': 'NutraPro',
        'sku': 'NP-PLN-204',
        'stock': 50,
        'rating': 4.5,
        'review_count': 98,
        'is_featured': False,
    },
]


class Command(BaseCommand):
    help = 'Seed the store with categories and sample products.'

    def handle(self, *args, **options):
        self.stdout.write('Seeding store catalog...')

        cat_map = {}
        for c in CATEGORIES:
            cat, _ = Category.objects.update_or_create(
                slug=c['slug'],
                defaults=c,
            )
            cat_map[c['slug']] = cat
        self.stdout.write(self.style.SUCCESS(f'  + {len(cat_map)} categories ready'))

        created = 0
        for p in PRODUCTS:
            cat_slug = p.pop('category')
            p['category'] = cat_map[cat_slug]
            _, was_created = Product.objects.update_or_create(
                sku=p['sku'],
                defaults=p,
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(
            f'  + {len(PRODUCTS)} products ready ({created} new)'
        ))
        self.stdout.write(self.style.SUCCESS('Store catalog seeded.'))
