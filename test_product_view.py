#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from django.test import Client

client = Client()
client.login(username='admin', password='admin123')

print("Testing product list view...")
response = client.get('/products/')
print(f"Status: {response.status_code}")

if response.status_code == 500:
    print("Error found! Content:")
    print(response.content.decode('utf-8', errors='ignore')[:1000])
else:
    print("View working correctly!")
    # Check if product_image URL is in response
    if b"product_image" in response.content:
        print("product_image URL found in response")
    else:
        print("WARNING: product_image URL not found in response")
