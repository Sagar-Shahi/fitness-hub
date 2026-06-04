from django.db import models
from django.utils.text import slugify
from django.urls import reverse


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    icon = models.CharField(max_length=8, default='', blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('store-product-list', kwargs={'category_slug': self.slug})


class Product(models.Model):
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='products'
    )
    short_description = models.CharField(max_length=240, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    compare_at_price = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    image_url = models.URLField(blank=True)
    brand = models.CharField(max_length=80, blank=True)
    sku = models.CharField(max_length=40, blank=True)
    stock = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    review_count = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['is_featured', 'is_active']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('store-product-detail', kwargs={'slug': self.slug})

    @property
    def in_stock(self):
        return self.stock > 0

    @property
    def discount_percent(self):
        if self.compare_at_price and self.compare_at_price > self.price:
            return int(round((1 - self.price / self.compare_at_price) * 100))
        return 0

    @property
    def is_on_sale(self):
        return self.discount_percent > 0


class Cart(models.Model):
    user = models.OneToOneField(
        'auth.User', on_delete=models.CASCADE, related_name='cart',
        null=True, blank=True,
    )
    session_key = models.CharField(max_length=40, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.user:
            return f"Cart #{self.pk} - {self.user.username}"
        return f"Cart #{self.pk} (session)"

    def subtotal(self):
        return sum(item.line_total() for item in self.items.select_related('product'))

    def item_count(self):
        return sum(item.quantity for item in self.items.all())

    def shipping(self):
        return 0 if self.subtotal() >= 50 else 4.99

    def tax(self):
        return round(float(self.subtotal()) * 0.08, 2)

    def total(self):
        return float(self.subtotal()) + float(self.shipping()) + float(self.tax())

    def is_empty(self):
        return not self.items.exists()


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'product')
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def line_total(self):
        return self.product.price * self.quantity


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_CHOICES = [
        ('card', 'Credit/Debit Card'),
        ('cod', 'Cash on Delivery'),
    ]

    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=20, unique=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default='card')

    full_name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    address = models.CharField(max_length=200)
    city = models.CharField(max_length=80)
    state = models.CharField(max_length=80)
    zip_code = models.CharField(max_length=20)
    country = models.CharField(max_length=80, default='United States')

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.order_number or f"Order #{self.pk}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            import uuid
            self.order_number = f"FH-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def item_count(self):
        return sum(item.quantity for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=160)
    product_price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product_name}"

    def line_total(self):
        return self.product_price * self.quantity
