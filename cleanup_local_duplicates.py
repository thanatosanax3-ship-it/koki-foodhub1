#!/usr/bin/env python
"""
Remove duplicate Ram product from local database
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from core.models import Product

print("Cleaning up duplicate Ram products...")
rams = Product.objects.filter(name='Ram', category='Main').order_by('id')
print(f"Found {rams.count()} Ram products")

ids_to_delete = list(rams.values_list('id', flat=True))[1:]
if ids_to_delete:
    Product.objects.filter(id__in=ids_to_delete).delete()
    print(f"✅ Deleted {len(ids_to_delete)} duplicate Ram products")
else:
    print("No duplicates to delete")

print(f"✅ Remaining Ram products: {Product.objects.filter(name='Ram', category='Main').count()}")
