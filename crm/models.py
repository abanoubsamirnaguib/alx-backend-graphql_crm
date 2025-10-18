from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
import re

# Create your models here.

class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True, validators=[
        RegexValidator(
            regex=r'^\+?\d{10,15}$|^\d{3}-\d{3}-\d{4}$',
            message="Phone number must be in format +1234567890 or 123-456-7890"
        )
    ])

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)

    def clean(self):
        if self.price <= 0:
            raise ValidationError("Price must be positive")
        if self.stock < 0:
            raise ValidationError("Stock cannot be negative")

    def __str__(self):
        return self.name

class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product)
    order_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        # Calculate total_amount as sum of product prices
        if self.pk is None:  # Only on creation
            self.total_amount = sum(product.price for product in self.products.all())
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.id} by {self.customer.name}"
