import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from core.models import Product

# Find products with images
products_with_images = Product.objects.exclude(image='')
print(f"\nProducts with images: {products_with_images.count()}")
for p in products_with_images[:10]:
    print(f"  {p.id}: {p.name} - {p.image.url}")

# Find Test Product
test_products = Product.objects.filter(name__icontains='test')
print(f"\nTest products: {test_products.count()}")
for p in test_products:
    print(f"  {p.id}: {p.name} - Image: {p.image.url if p.image else 'None'}")
