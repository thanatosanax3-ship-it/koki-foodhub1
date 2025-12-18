import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from core.models import Product
from django.utils import timezone

# Find products with null created_at and set them
products_without_date = Product.objects.filter(created_at__isnull=True)
print(f"Found {products_without_date.count()} products without created_at\n")

for product in products_without_date:
    product.created_at = timezone.now()
    product.save()
    print(f"Updated: {product.name} (ID: {product.id})")

print(f"\nDone! All {products_without_date.count()} products now have created_at set.")
