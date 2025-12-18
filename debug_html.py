#!/usr/bin/env python
"""
Test to check if products are properly initialized in the dashboard HTML
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User

# Create a test user
test_user, created = User.objects.get_or_create(
    username='testuser',
    defaults={'email': 'test@test.com'}
)
if created:
    test_user.set_password('testpass123')
    test_user.save()

client = Client()
# Log in the user
client.login(username='testuser', password='testpass123')
response = client.get('/')

if response.status_code == 200:
    html = response.content.decode('utf-8')
    
    # Find the products initialization section
    import re
    
    # Find all product definitions
    product_defs = re.findall(r'products\[\d+\]\s*=\s*\{[^}]+\}', html)
    print(f"Found {len(product_defs)} product definitions in JavaScript")
    
    if product_defs:
        print("\nFirst product definition:")
        print(product_defs[0])
    
    # Check if handleProductClick exists
    if 'function handleProductClick' in html:
        print("\n✓ handleProductClick function exists")
        
        # Extract the function
        match = re.search(r'function handleProductClick\(event, productId\)\s*\{[^}]*\}', html, re.DOTALL)
        if match:
            func = match.group(0)
            print("\nFunction code (first 500 chars):")
            print(func[:500])
    else:
        print("\n✗ handleProductClick function NOT found")
    
    # Check onclick handlers
    onclick_count = len(re.findall(r'onclick="handleProductClick', html))
    print(f"\n✓ Found {onclick_count} onclick handlers on product cards")
    
    # Check products object initialization
    if 'const products = {}' in html:
        print("✓ products object initialization found")
    
    # Get first product card HTML
    product_card = re.search(r'<div class="product-card"[^>]*>.*?</div>', html, re.DOTALL)
    if product_card:
        card_html = product_card.group(0)[:300]
        print("\nFirst product card (first 300 chars):")
        print(card_html)
else:
    print(f"Error: Status code {response.status_code}")
