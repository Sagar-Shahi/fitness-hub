from django.db import models
from django.utils.text import slugify


class Product(models.Model):
    TYPE_OUTFIT = 'outfit'
    TYPE_EXERCISE = 'exercise'
    TYPE_NUTRITION = 'nutrition'

    TYPE_CHOICES = [
        (TYPE_OUTFIT, 'Outfit Products'),
        (TYPE_EXERCISE, 'Exercise Products'),
        (TYPE_NUTRITION, 'Nutrition Products'),
    ]

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)
    product_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_OUTFIT)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    image_url = models.URLField(blank=True)

    class Meta:
        ordering = ['product_type', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Cart(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='carts')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart {self.id} - {self.user.username}"


class Order(models.Model):
    STATUS = (('pending', 'Pending'), ('paid', 'Paid'), ('shipped', 'Shipped'))
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS, default='pending')

    def __str__(self):
        return f"Order {self.id} - {self.user.username}"
