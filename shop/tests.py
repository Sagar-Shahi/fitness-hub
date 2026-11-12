from decimal import Decimal

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from tracker.testutils import make_user

from .models import CartItem, Order, OrderItem, Plan


def make_plan(title='Plan', price='9.00', **extra):
    values = {'kind': 'workout', 'summary': 'Short summary', 'content': 'SECRET-FULL-CONTENT', 'price': Decimal(price)}
    values.update(extra)
    return Plan.objects.create(title=title, **values)


class Base(TestCase):
    def setUp(self):
        cache.clear()
        self.user = make_user('sam')
        self.client.force_login(self.user)
        self.a = make_plan('Plan A', '9.00')
        self.b = make_plan('Plan B', '14.50', kind='diet')


class PlanModelTests(TestCase):
    def test_slugs_are_unique_and_generated(self):
        one, two = make_plan('Same Title'), make_plan('Same Title')
        self.assertEqual((one.slug, two.slug), ('same-title', 'same-title-2'))

    def test_a_title_of_symbols_still_gets_a_slug(self):
        self.assertEqual(make_plan('!!!').slug, 'plan')


class CatalogueTests(Base):
    def test_list_and_filter(self):
        body = self.client.get(reverse('shop:plans')).content.decode()
        self.assertIn('Plan A', body); self.assertIn('Plan B', body)
        diet = self.client.get(reverse('shop:plans'), {'kind': 'diet'}).content.decode()
        self.assertIn('Plan B', diet); self.assertNotIn('Plan A', diet)
        self.assertEqual(self.client.get(reverse('shop:plans'), {'kind': "x'; --"}).status_code, 200)

    def test_inactive_plans_are_hidden_everywhere(self):
        Plan.objects.filter(pk=self.a.pk).update(is_active=False)
        self.assertNotContains(self.client.get(reverse('shop:plans')), 'Plan A')
        self.assertEqual(self.client.get(reverse('shop:plan-detail', args=[self.a.slug])).status_code, 404)
        self.assertEqual(self.client.post(reverse('shop:cart-add', args=[self.a.slug])).status_code, 404)

    def test_the_full_content_is_hidden_until_bought(self):
        response = self.client.get(reverse('shop:plan-detail', args=[self.a.slug]))
        self.assertNotContains(response, 'SECRET-FULL-CONTENT')
        self.assertContains(response, 'unlocks after checkout')
        self.assertNotContains(self.client.get(reverse('shop:plans')), 'SECRET-FULL-CONTENT')


class CartTests(Base):
    def test_add_is_post_only_and_idempotent(self):
        url = reverse('shop:cart-add', args=[self.a.slug])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.post(url); self.client.post(url)
        self.assertEqual(CartItem.objects.filter(owner=self.user).count(), 1)

    def test_total_uses_database_prices(self):
        self.client.post(reverse('shop:cart-add', args=[self.a.slug]))
        self.client.post(reverse('shop:cart-add', args=[self.b.slug]))
        response = self.client.get(reverse('shop:cart'))
        self.assertEqual(response.context['total'], Decimal('23.50'))
        self.assertContains(response, '$23.50')

    def test_remove(self):
        self.client.post(reverse('shop:cart-add', args=[self.a.slug]))
        self.client.post(reverse('shop:cart-remove', args=[self.a.slug]))
        self.assertEqual(CartItem.objects.count(), 0)

    def test_carts_are_private(self):
        other = make_user('other')
        CartItem.objects.create(owner=other, plan=self.b)
        self.assertEqual(self.client.get(reverse('shop:cart')).context['items'], [])
        self.client.post(reverse('shop:cart-remove', args=[self.b.slug]))
        self.assertEqual(CartItem.objects.filter(owner=other).count(), 1)

    def test_the_menu_shows_the_cart_count(self):
        self.client.post(reverse('shop:cart-add', args=[self.a.slug]))
        self.assertContains(self.client.get(reverse('tracker:goals')), 'Cart (1)')


class CheckoutTests(Base):
    def _fill(self, *plans):
        for plan in plans:
            CartItem.objects.create(owner=self.user, plan=plan)

    def test_checkout_creates_an_order_with_snapshots_and_empties_the_cart(self):
        self._fill(self.a, self.b)
        response = self.client.post(reverse('shop:checkout'))
        order = Order.objects.get()
        self.assertRedirects(response, reverse('shop:order-detail', args=[order.reference]))
        self.assertEqual((order.owner, order.total), (self.user, Decimal('23.50')))
        self.assertEqual(sorted(i.title for i in order.items.all()), ['Plan A', 'Plan B'])
        self.assertEqual(CartItem.objects.count(), 0)
        self.assertRegex(order.reference, r'^FH-[0-9A-F]{8}$')

    def test_the_price_comes_from_the_server_not_the_request(self):
        self._fill(self.a)
        self.client.post(reverse('shop:checkout'), {'total': '0.01', 'price': '0.01', 'plan': self.b.pk})
        order = Order.objects.get()
        self.assertEqual(order.total, Decimal('9.00'))
        self.assertEqual([i.plan for i in order.items.all()], [self.a])

    def test_later_price_changes_do_not_rewrite_history(self):
        self._fill(self.a)
        self.client.post(reverse('shop:checkout'))
        Plan.objects.filter(pk=self.a.pk).update(price=Decimal('99.00'), title='Renamed')
        item = OrderItem.objects.get()
        self.assertEqual((item.price, item.title), (Decimal('9.00'), 'Plan A'))
        self.assertEqual(Order.objects.get().total, Decimal('9.00'))

    def test_empty_cart(self):
        response = self.client.post(reverse('shop:checkout'), follow=True)
        self.assertContains(response, 'Your cart is empty')
        self.assertEqual(Order.objects.count(), 0)

    def test_get_is_not_allowed(self):
        self.assertEqual(self.client.get(reverse('shop:checkout')).status_code, 405)

    def test_plans_you_already_own_are_not_charged_twice(self):
        self._fill(self.a)
        self.client.post(reverse('shop:checkout'))
        CartItem.objects.create(owner=self.user, plan=self.a)  # e.g. added from a second tab
        self.client.post(reverse('shop:checkout'))
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(self.client.post(reverse('shop:cart-add', args=[self.a.slug]), follow=True).status_code, 200)
        self.assertEqual(CartItem.objects.filter(owner=self.user, plan=self.a).count(), 1)  # the stale line is left, but no second order

    def test_buying_unlocks_the_content(self):
        self._fill(self.a)
        self.client.post(reverse('shop:checkout'))
        self.assertContains(self.client.get(reverse('shop:plan-detail', args=[self.a.slug])), 'SECRET-FULL-CONTENT')
        self.assertContains(self.client.get(reverse('shop:my-plans')), 'Plan A')

    def test_someone_else_does_not_get_the_content(self):
        self._fill(self.a)
        self.client.post(reverse('shop:checkout'))
        other = make_user('other')
        self.client.force_login(other)
        self.assertNotContains(self.client.get(reverse('shop:plan-detail', args=[self.a.slug])), 'SECRET-FULL-CONTENT')
        self.assertNotContains(self.client.get(reverse('shop:my-plans')), 'Plan A')

    @override_settings(CHECKOUT_MAX_PER_HOUR=2)
    def test_checkout_is_rate_limited(self):
        statuses = []
        for _ in range(4):
            statuses.append(self.client.post(reverse('shop:checkout')).status_code)
        self.assertEqual(statuses, [302, 302, 429, 429])

    def test_the_demo_is_clearly_labelled(self):
        self._fill(self.a)
        self.assertContains(self.client.get(reverse('shop:cart')), 'No payment provider is connected')


class OrderPrivacyTests(Base):
    def test_other_users_orders_are_404(self):
        other = make_user('other')
        order = Order.objects.create(owner=other, total=Decimal('9.00'))
        OrderItem.objects.create(order=order, plan=self.a, title='Plan A', price=Decimal('9.00'))
        self.assertEqual(self.client.get(reverse('shop:order-detail', args=[order.reference])).status_code, 404)
        self.assertNotContains(self.client.get(reverse('shop:orders')), order.reference)
        self.assertEqual(self.client.get(reverse('shop:order-detail', args=['FH-NOPE'])).status_code, 404)
