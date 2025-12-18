#!/usr/bin/env python
"""
Test script to verify products are rendering correctly in the dashboard
"""
import os
import django
from django.test import Client

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from core.models import Product

if __name__ == '__main__':
    # Check if products exist
    products = Product.objects.all()
    print(f"Total products in database: {products.count()}")
    for product in products[:5]:
        qty = getattr(product, 'quantity', 'N/A')
        print(f"  - {product.id}: {product.name} (Qty: {qty})")

    # Test the dashboard view
    print("\nTesting dashboard view...")
    client = Client()
    response = client.get('/dashboard/')
    print(f"Status code: {response.status_code}")

    if response.status_code == 200:
        # Check if products are in the response
        if 'all_products' in response.context:
            products_in_context = response.context['all_products']
            print(f"Products in context: {len(products_in_context)}")
            
            # Check if handleProductClick is in the HTML
            html = response.content.decode('utf-8')
            if 'handleProductClick' in html:
                print("✓ handleProductClick function found in HTML")
            else:
                print("✗ handleProductClick function NOT found in HTML")
            
            if 'onclick="handleProductClick' in html:
                print("✓ onclick handlers found on product cards")
            else:
                print("✗ onclick handlers NOT found on product cards")
                
            # Check if products object is initialized
            if 'const products = {}' in html:
                print("✓ products object initialization found")
            else:
                print("✗ products object initialization NOT found")
                
            # Count how many product cards are rendered
            import re
            product_cards = len(re.findall(r'<div class="product-card"', html))
            print(f"✓ Found {product_cards} product cards in HTML")
        else:
            print("No 'all_products' in context!")
    else:
        print(f"Failed to load dashboard: {response.status_code}")
        print(response.content.decode('utf-8')[:500])
