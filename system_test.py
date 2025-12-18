#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Comprehensive system functionality test"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from django.test import Client
from core.models import Product, InventoryItem, Sale
from django.contrib.auth.models import User
from django.urls import reverse
import json

print("=" * 60)
print("COMPREHENSIVE SYSTEM TEST")
print("=" * 60)

# Test 1: Database Models
print("\n[1] DATABASE MODELS")
print("-" * 60)
try:
    products = Product.objects.all()
    print(f"✓ Products: {products.count()} items")
    if products.exists():
        p = products.first()
        print(f"  - Sample: {p.name} (ID: {p.id}, has_image: {bool(p.image)})")
except Exception as e:
    print(f"✗ Products error: {e}")

try:
    users = User.objects.all()
    print(f"✓ Users: {users.count()} accounts")
    if users.exists():
        u = users.first()
        print(f"  - Sample: {u.username} ({u.get_full_name()})")
except Exception as e:
    print(f"✗ Users error: {e}")

try:
    inventory = InventoryItem.objects.all()
    print(f"✓ Inventory: {inventory.count()} items")
except Exception as e:
    print(f"✗ Inventory error: {e}")

try:
    sales = Sale.objects.all()
    print(f"✓ Sales: {sales.count()} records")
except Exception as e:
    print(f"✗ Sales error: {e}")

# Test 2: URL Routes
print("\n[2] URL ROUTES")
print("-" * 60)
client = Client()
test_urls = [
    ('/', 'Home'),
    ('/products/', 'Products'),
    ('/dashboard/', 'Dashboard'),
    ('/inventory/', 'Inventory'),
    ('/sales/', 'Sales'),
]

for url, name in test_urls:
    try:
        response = client.get(url)
        status = "✓" if response.status_code in [200, 302, 405] else "✗"
        print(f"{status} {name:20} {url:30} -> {response.status_code}")
    except Exception as e:
        print(f"✗ {name:20} {url:30} -> Error: {str(e)[:30]}")

# Test 3: Template Rendering
print("\n[3] TEMPLATE RENDERING")
print("-" * 60)
try:
    response = client.get('/products/')
    if response.status_code == 200:
        if b'addProductModal' in response.content or b'productGrid' in response.content:
            print("✓ Product list template renders correctly")
        else:
            print("⚠ Product template might be missing elements")
    else:
        print(f"✗ Product template failed: {response.status_code}")
except Exception as e:
    print(f"✗ Template test error: {e}")

# Test 4: Static Files
print("\n[4] STATIC FILES")
print("-" * 60)
from django.conf import settings
static_files = [
    ('styles.css', 'CSS'),
    ('service-worker.js', 'Service Worker'),
]

for filename, desc in static_files:
    path = os.path.join(settings.STATIC_ROOT, filename) if hasattr(settings, 'STATIC_ROOT') else None
    if path and os.path.exists(path):
        size = os.path.getsize(path)
        print(f"✓ {desc:20} ({filename:30}) {size} bytes")
    else:
        print(f"⚠ {desc:20} ({filename:30}) might not be collected")

# Test 5: Media Files
print("\n[5] MEDIA FILES")
print("-" * 60)
media_root = settings.MEDIA_ROOT
if os.path.exists(media_root):
    print(f"✓ Media root exists: {media_root}")
    media_dir = os.path.join(media_root, 'products')
    if os.path.exists(media_dir):
        image_count = len([f for f in os.listdir(media_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))])
        print(f"✓ Product images: {image_count} files")
    else:
        print(f"⚠ Products directory missing (will be created on upload)")
else:
    print(f"✗ Media root missing: {media_root}")

# Test 6: Settings Validation
print("\n[6] SETTINGS VALIDATION")
print("-" * 60)
print(f"✓ DEBUG: {settings.DEBUG}")
print(f"✓ ALLOWED_HOSTS: {len(settings.ALLOWED_HOSTS)} hosts")
print(f"✓ FILE_CHARSET: {settings.FILE_CHARSET}")
print(f"✓ DEFAULT_CHARSET: {settings.DEFAULT_CHARSET}")
print(f"✓ DATABASE: {settings.DATABASES['default']['ENGINE'].split('.')[-1]}")

print("\n" + "=" * 60)
print("SYSTEM TEST COMPLETE")
print("=" * 60)
