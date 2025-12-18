#!/usr/bin/env python
"""
Test the payment API locally
"""
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from core.models import Product, Sale
from django.test import Client
from django.contrib.auth.models import User, Group

print("Testing Payment API\n" + "="*50)

# Check database state
print("\n1. Database State:")
print(f"   Total Products: {Product.objects.count()}")
print(f"   Total Sales: {Sale.objects.count()}")

# Get first product
p = Product.objects.first()
if p:
    print(f"\n2. First Product:")
    print(f"   Name: {p.name}")
    print(f"   ID: {p.id}")
    print(f"   Price: {p.price}")
    
    inv = p.inventory_items.first()
    if inv:
        print(f"   Inventory: {inv.quantity}")
    else:
        print(f"   Inventory: NONE - This is the problem!")
else:
    print("   No products found!")

# Test API
print(f"\n3. Testing Payment API:")
client = Client()

# Get or create admin user
admin_user, created = User.objects.get_or_create(username='testadmin', defaults={'is_staff': True})
if created:
    admin_user.set_password('testpass')
    admin_user.save()
admin_group, _ = Group.objects.get_or_create(name='Admin')
admin_user.groups.add(admin_group)

# Login
client.login(username='testadmin', password='testpass')
print(f"   Logged in as: testadmin")

# Create test payload
payload = {
    'items': [
        {
            'id': p.id if p else 1,
            'name': p.name if p else 'Test Product',
            'price': float(p.price) if p else 10.0,
            'quantity': 1
        }
    ]
}

print(f"   Payload: {json.dumps(payload, indent=2)}")

# Get CSRF token from a GET request first
from django.middleware.csrf import get_token
from django.test import RequestFactory
csrf_token = 'test-token-skip'  # For API, CSRF is checked differently

print(f"   CSRF Token: test-token-skip")

# Make request
response = client.post('/sales/api/create/', 
    data=json.dumps(payload),
    content_type='application/json',
    HTTP_X_CSRFTOKEN=csrf_token
)

print(f"\n4. API Response:")
print(f"   Status: {response.status_code}")
print(f"   Content-Type: {response.get('Content-Type')}")
try:
    data = json.loads(response.content)
    print(f"   Body: {json.dumps(data, indent=2)}")
except:
    print(f"   Body: {response.content[:500]}")

print("\n" + "="*50)
