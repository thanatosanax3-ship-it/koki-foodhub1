import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from core.models import Product, InventoryItem

# Get a product with size
product_with_size = Product.objects.exclude(size='').exclude(size__isnull=True).first()
print(f"Product with size: {product_with_size.id} - {product_with_size.name} (Size: {product_with_size.size})")
print(f"Price: {product_with_size.price}")
print(f"Size prices:")
print(f"  - Small: {product_with_size.price_small}")
print(f"  - Medium: {product_with_size.price_medium}")
print(f"  - Large: {product_with_size.price_large}")
print(f"  - XL: {product_with_size.price_xl}")
print(f"  - XXL: {product_with_size.price_xxl}")
print(f"  - Regular: {product_with_size.price_regular}")

# Check inventory
inv = product_with_size.inventory_items.first()
if inv:
    print(f"\nInventory: {inv.quantity} units (SKU: {inv.sku})")
else:
    print("\nNo inventory item found!")
