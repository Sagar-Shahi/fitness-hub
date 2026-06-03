from django.test import TestCase
from django.urls import reverse
from .models import Product


class StoreTests(TestCase):
    def setUp(self):
        Product.objects.create(
            name='Test Training Tank',
            slug='test-training-tank',
            description='Lightweight outfit for gym sessions.',
            product_type=Product.TYPE_OUTFIT,
            price=19.99,
        )

    def test_store_home(self):
        resp = self.client.get(reverse('store-home'))
        self.assertEqual(resp.status_code, 200)

    def test_outfit_product_list(self):
        resp = self.client.get(reverse('store-product-list', args=[Product.TYPE_OUTFIT]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Test Training Tank')

    def test_outfit_product_detail(self):
        resp = self.client.get(reverse('store-product-detail', args=[Product.TYPE_OUTFIT, 'test-training-tank']))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Lightweight outfit for gym sessions.')
