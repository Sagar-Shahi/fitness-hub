from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Product


class StoreTests(TestCase):
    def setUp(self):
        Product.objects.create(name='Test Prod', slug='test-prod', price=9.99)

    def test_product_list(self):
        resp = self.client.get(reverse('product-list'))
        self.assertEqual(resp.status_code, 200)

    def test_add_to_cart_session(self):
        resp = self.client.post(reverse('add-to-cart', args=['test-prod']), {'quantity': 2})
        # should redirect back to detail
        self.assertEqual(resp.status_code, 302)
        session = self.client.session
        self.assertIn('cart', session)
        self.assertEqual(session['cart'].get('test-prod'), 2)
from django.test import TestCase

# Create your tests here.
