import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from core.models import Product

products = Product.objects.all()
print(f"Total products: {products.count()}")
for p in products:
    image_info = p.image.url if p.image else "No image"
    print(f"  {p.id}: {p.name} - {image_info}")
