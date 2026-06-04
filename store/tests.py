from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from .models import Category, Product, Order


class StoreModelTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name='Outfits', slug='outfits')
        self.product = Product.objects.create(
            name='Performance Tee', slug='performance-tee',
            category=self.cat, price=29.99, stock=10, is_active=True,
        )

    def test_discount_percent_with_compare_price(self):
        self.product.compare_at_price = 49.99
        self.product.save()
        self.assertEqual(self.product.discount_percent, 40)
        self.assertTrue(self.product.is_on_sale)

    def test_discount_percent_without_compare_price(self):
        self.assertEqual(self.product.discount_percent, 0)
        self.assertFalse(self.product.is_on_sale)

    def test_product_in_stock(self):
        self.assertTrue(self.product.in_stock)
        self.product.stock = 0
        self.assertFalse(self.product.in_stock)

    def test_order_number_generated(self):
        order = Order.objects.create(
            user=User.objects.create_user('alice', 'a@a.com', 'pw'),
            full_name='Alice', email='a@a.com', address='1 St',
            city='NY', state='NY', zip_code='10001',
            subtotal=10, total=10,
        )
        self.assertTrue(order.order_number.startswith('FH-'))


class StoreViewTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name='Gear', slug='gear')
        self.product = Product.objects.create(
            name='Kettlebell', slug='kettlebell', category=self.cat,
            price=49.99, stock=5, is_active=True,
        )

    def test_store_home(self):
        resp = self.client.get(reverse('store-home'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Gear')

    def test_product_list(self):
        resp = self.client.get(reverse('store-product-list'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Kettlebell')

    def test_product_list_by_category(self):
        resp = self.client.get(reverse('store-category', args=['gear']))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Kettlebell')

    def test_product_detail(self):
        resp = self.client.get(reverse('store-product-detail', args=['kettlebell']))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '49.99')

    def test_search(self):
        resp = self.client.get(reverse('store-product-list'), {'q': 'Kettle'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Kettlebell')

    def test_sort(self):
        resp = self.client.get(reverse('store-product-list'), {'sort': 'price_low'})
        self.assertEqual(resp.status_code, 200)

    def test_cart_view(self):
        resp = self.client.get(reverse('view-cart'))
        self.assertEqual(resp.status_code, 200)

    def test_add_to_cart_creates_item(self):
        resp = self.client.post(reverse('add-to-cart', args=['kettlebell']))
        self.assertRedirects(resp, reverse('view-cart'))
        # Verify cart now has item
        resp = self.client.get(reverse('view-cart'))
        self.assertContains(resp, 'Kettlebell')

    def test_remove_from_cart(self):
        self.client.post(reverse('add-to-cart', args=['kettlebell']))
        # Get the item id from cart
        from .models import Cart
        cart = Cart.objects.first()
        item_id = cart.items.first().pk
        self.client.get(reverse('remove-from-cart', args=[item_id]))
        self.assertFalse(cart.items.exists())

    def test_checkout_requires_login(self):
        resp = self.client.get(reverse('checkout'))
        self.assertEqual(resp.status_code, 302)

    def test_order_history_requires_login(self):
        resp = self.client.get(reverse('order-history'))
        self.assertEqual(resp.status_code, 302)
