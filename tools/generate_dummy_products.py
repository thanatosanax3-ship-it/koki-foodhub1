#!/usr/bin/env python3
"""Generate dummy products for local visual testing.

Usage: python tools/generate_dummy_products.py [count]
"""
import os
import sys
from decimal import Decimal

# Ensure project root is on sys.path so Django package can be imported when run from tools/
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
    try:
        import django
        django.setup()
    except Exception as e:
        print('Error setting up Django:', e)
        sys.exit(1)

    from core.models import Product
    from django.utils import timezone

    try:
        count = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    except ValueError:
        count = 30

    categories = ['Main', 'Appetizer', 'Beverage', 'Dessert', 'Snacks', 'Sides']

    created = 0
    base_names = ['Pizza', 'Burger', 'Fries', 'Taco', 'Salad', 'Sushi', 'Pasta', 'Soup', 'Sandwich', 'Wrap']
    for i in range(count):
        name = f"{base_names[i % len(base_names)]} #{i+1}"
        price = Decimal(str(20 + (i % 10) * 5 + (i % 3) * 0.5))
        cat = categories[i % len(categories)]

        # Avoid creating duplicates if same name exists
        if Product.objects.filter(name=name).exists():
            continue

        p = Product.objects.create(
            name=name,
            category=cat,
            price=price,
            created_at=timezone.now(),
        )
        created += 1

    print(f'Created {created} products (requested {count}).')


if __name__ == '__main__':
    main()
