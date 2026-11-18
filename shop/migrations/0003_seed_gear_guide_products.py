from django.db import migrations


PRODUCTS = [
    {
        "title": "Pull Up Assist Band Set (4 Pieces)",
        "slug": "pull-up-assist-band-set-of-4",
        "category": "accessories",
        "description": "A four-band latex set listed with different resistance levels, 183 cm length and 4.5 mm thickness. Check the retailer page for current options and price.",
        "seller_name": "Fitmandu",
        "seller_url": "https://fitmandu.com/products/68JFuFxt6ctbwivh",
        "featured": True,
    },
    {
        "title": "Yogpro 6 mm Yoga Mat with Carry Bag",
        "slug": "yogpro-yoga-mat-with-carry-bag",
        "category": "accessories",
        "description": "A 6 ft by 2 ft mat listed as 6 mm thick, with a carry bag and double-sided grip. Check the retailer page for current options and price.",
        "seller_name": "Fitmandu",
        "seller_url": "https://fitmandu.com/products/BvzTj2VueA0yEwa7",
        "featured": True,
    },
    {
        "title": "Rubber Hex Dumbbell 5 kg Pair",
        "slug": "rubber-hex-dumbbell-5kg-pair",
        "category": "equipment",
        "description": "A rubber hex dumbbell pair listed in a 5 kg option. The retailer page also describes other size options; confirm the selected weight before ordering.",
        "seller_name": "Fitmandu",
        "seller_url": "https://fitmandu.com/products/tWgnG8GmNDpgaX7k",
        "featured": True,
    },
    {
        "title": "20 kg Adjustable Dumbbell Set with Barbell Connector",
        "slug": "20kg-adjustable-dumbbell-set-mega-shop-nepal",
        "category": "equipment",
        "description": "An adjustable set listing multiple plate weights, two dumbbell rods, screws and a 40 cm connector. Check the retailer page for current price, shipping and availability.",
        "seller_name": "Mega Shop Nepal",
        "seller_url": "https://www.megashop.com.np/product/20kg-dumbbell-adjustable-set-pvc-%2B-barbell-connector-by-mega-shop-nepal",
        "featured": False,
    },
    {
        "title": "EVA Yoga Mat 8 mm with Carrying Bag",
        "slug": "eva-yoga-mat-8mm-mega-shop-nepal",
        "category": "accessories",
        "description": "An EVA mat listed at 8 mm thick and 6 ft by 2 ft, with a carrying bag. The retailer page currently shows no customer reviews; check details before ordering.",
        "seller_name": "Mega Shop Nepal",
        "seller_url": "https://www.megashop.com.np/product/eco-friendly-travel-eva-foam-yoga-mat-8mm-with-carrying-bag-6ft-x-2ft-x-0.8mm",
        "featured": False,
    },
]


def add_products(apps, schema_editor):
    Product = apps.get_model("shop", "AffiliateProduct")
    for item in PRODUCTS:
        Product.objects.get_or_create(slug=item["slug"], defaults={
            **item,
            "is_active": True,
            "price_label": "",
            "affiliate_url": "",
        })


def remove_products(apps, schema_editor):
    Product = apps.get_model("shop", "AffiliateProduct")
    Product.objects.filter(slug__in=[item["slug"] for item in PRODUCTS]).delete()


class Migration(migrations.Migration):
    dependencies = [("shop", "0002_affiliateproduct")]

    operations = [migrations.RunPython(add_products, remove_products)]
