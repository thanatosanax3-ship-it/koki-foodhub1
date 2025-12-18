# core/models.py
from django.db import models
from django.utils import timezone

class Product(models.Model):
    SIZE_CHOICES = [
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
        ('XL', 'Extra Large'),
        ('XXL', 'XXL'),
        ('Regular', 'Regular'),
    ]
    
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=80, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    size = models.CharField(max_length=20, choices=SIZE_CHOICES, blank=True, null=True, help_text="Leave blank if product doesn't have sizes")
    
    # Size-specific prices (only used if size is set)
    price_small = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_medium = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_large = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_xl = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_xxl = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_regular = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True, db_index=True)

    def __str__(self):
        return self.name
    
    def get_price_for_size(self, size):
        """Return the price for a given size, or fallback to base price"""
        if not size:
            return self.price
        
        size_price_map = {
            'S': self.price_small,
            'M': self.price_medium,
            'L': self.price_large,
            'XL': self.price_xl,
            'XXL': self.price_xxl,
            'Regular': self.price_regular,
        }
        
        size_price = size_price_map.get(size)
        return size_price if size_price is not None else self.price

class InventoryItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="inventory_items")
    sku = models.CharField(max_length=64, unique=True)
    quantity = models.PositiveIntegerField(default=0)
    reorder_point = models.PositiveIntegerField(default=10)
    size = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
        ('XL', 'Extra Large'),
        ('XXL', 'XXL'),
        ('Regular', 'Regular'),
    ])
    updated_at = models.DateTimeField(auto_now=True)

    def is_low_stock(self):
        return self.quantity <= self.reorder_point

    def __str__(self):
        return f"{self.sku} - {self.product.name}"

class Sale(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="sales")
    date = models.DateField(default=timezone.now)
    units_sold = models.PositiveIntegerField()
    revenue = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.product.name} - {self.date} - {self.units_sold}"
