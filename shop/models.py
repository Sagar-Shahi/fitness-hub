import secrets
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify

MONEY = Decimal('0.01')
KINDS = [('workout', 'Training plan'), ('diet', 'Diet plan')]


class Plan(models.Model):
    """A training or diet plan for sale. Managed in the admin; the full content is shown only to buyers."""

    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=110, unique=True, blank=True)
    kind = models.CharField(max_length=10, choices=KINDS)
    summary = models.CharField(max_length=280)
    content = models.TextField(help_text='The full plan. Only people who bought it can read this.')
    price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(MONEY)])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['kind', 'price', 'title']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:100] or 'plan'
            slug, n = base, 2
            while Plan.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug, n = f'{base}-{n}', n + 1
            self.slug = slug
        super().save(*args, **kwargs)


class CartItem(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart_items')
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['owner', 'plan'], name='one_cart_line_per_plan')]
        ordering = ['added_at']


def new_reference():
    return 'FH-' + secrets.token_hex(4).upper()


class Order(models.Model):
    """DEMO checkout: no payment provider is connected, so no money is ever taken."""

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    reference = models.CharField(max_length=16, unique=True, default=new_reference, editable=False)
    total = models.DecimalField(max_digits=9, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']

    def __str__(self):
        return self.reference


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name='order_items')
    title = models.CharField(max_length=100)  # snapshots, so later price or title changes never rewrite history
    price = models.DecimalField(max_digits=8, decimal_places=2)
