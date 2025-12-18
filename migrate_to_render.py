"""
Script to migrate local database data to Render deployed database
Usage: python migrate_to_render.py
"""
import os
import json
import django
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Product
from django.core.serializers import serialize

print("\n" + "="*70)
print("🚀 LOCAL DATABASE → RENDER MIGRATION")
print("="*70)

# Step 1: Export data
print("\n→ Exporting data from local database...")

users_data = serialize('json', User.objects.all())
products_data = serialize('json', Product.objects.all())

# Save to files
with open('users_export.json', 'w') as f:
    f.write(users_data)
print(f"✅ Exported {User.objects.count()} users")

with open('products_export.json', 'w') as f:
    f.write(products_data)
print(f"✅ Exported {Product.objects.count()} products")

print("\n" + "="*70)
print("📋 MIGRATION DATA READY")
print("="*70)
print("\nNext steps:")
print("1. Run migrations on Render: python manage.py migrate")
print("2. Upload users_export.json and products_export.json to Render")
print("3. Run: python manage.py loaddata users_export.json products_export.json")
print("\nOr use this one-liner after uploading files:")
print("  python manage.py loaddata users_export.json products_export.json\n")
