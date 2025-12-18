#!/usr/bin/env python
"""
Populate inventory with all products
Creates InventoryItem entries for each product to track stock levels
"""
import os
import sys
import django
from django.db.models import Count

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')

# Get DATABASE_URL from command line or environment
if len(sys.argv) > 1:
    os.environ['DATABASE_URL'] = sys.argv[1]

django.setup()

from core.models import Product, InventoryItem

print("\n" + "="*70)
print("📦 POPULATING INVENTORY FROM PRODUCTS")
print("="*70)

# Get all products
products = Product.objects.all()
total_products = products.count()

print(f"\n→ Found {total_products} products to add to inventory...")

created_count = 0
skipped_count = 0

for product in products:
    # Check if inventory item already exists
    inventory_exists = InventoryItem.objects.filter(product=product).exists()
    
    if not inventory_exists:
        # Generate SKU from product name and id
        sku = f"{product.name.lower().replace(' ', '_')[:20]}_{product.id}"
        
        # Create inventory item with default quantities
        inventory_item = InventoryItem.objects.create(
            product=product,
            sku=sku,
            quantity=50,  # Default starting quantity
            reorder_point=10  # Alert when stock falls below 10
        )
        created_count += 1
        print(f"   ✓ {product.name} - SKU: {sku}")
    else:
        skipped_count += 1

print(f"\n📊 Inventory Population Summary:")
print(f"   ✅ Created: {created_count} inventory items")
print(f"   ⏭️  Skipped: {skipped_count} (already exist)")

# Display inventory stats
print(f"\n📋 Inventory Statistics:")
inventory_items = InventoryItem.objects.all()
total_inventory = inventory_items.count()
total_stock = sum(item.quantity for item in inventory_items)
low_stock_items = inventory_items.filter(quantity__lte=10).count()

print(f"   Total Inventory Items: {total_inventory}")
print(f"   Total Stock Units: {total_stock}")
print(f"   Low Stock Items (≤10): {low_stock_items}")

# Show categories with inventory
print(f"\n📂 Inventory by Category:")
categories = Product.objects.values('category').annotate(count=Count('id')).order_by('category')
for cat in categories:
    cat_inventory = inventory_items.filter(product__category=cat['category']).count()
    print(f"   - {cat['category']}: {cat_inventory} items")

print("\n" + "="*70)
print("✅ INVENTORY POPULATION COMPLETE")
print("="*70 + "\n")
