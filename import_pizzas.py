import os
import django
import pandas as pd
import uuid
import urllib.request
from pathlib import Path
import argparse

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from urllib.error import URLError

from core.models import Product, InventoryItem

# Configuration: local images folder (optional)
LOCAL_IMAGE_DIR = Path('product_images')  # place images here, filenames may match product names

parser = argparse.ArgumentParser(description='Import pizzas from CSV')
parser.add_argument('--limit', type=int, default=0, help='Maximum number of CSV rows to process (0 = no limit)')
parser.add_argument('--unique', action='store_true', help='Import unique products by name only')
parser.add_argument('--allow-duplicates', action='store_true', help='Create products even if name already exists')
parser.add_argument('--csv', default='pizzaplace.csv', help='Path to CSV file')
args = parser.parse_args()

# Read CSV
df = pd.read_csv(args.csv)

# Optionally limit rows
if args.limit and args.limit > 0:
    df = df.head(args.limit)

# Get products to process (unique by name if requested)
if args.unique:
    products_df = df.drop_duplicates(subset=['name']).sort_values('name')
else:
    products_df = df.copy()

# Category mapping from 'type' column
category_map = {
    'classic': 'Main',
    'veggie': 'Appetizer',
    'chicken': 'Main',
    'supreme': 'Main'
}

def find_local_image(product_name):
    """Try common filename variants in LOCAL_IMAGE_DIR and return path or None."""
    if not LOCAL_IMAGE_DIR.exists():
        return None
    base = product_name.replace('_', ' ').strip()
    candidates = [
        base,
        base.replace(' ', '_'),
        base.replace(' ', '-'),
        base.lower(),
    ]
    exts = ['.jpg', '.jpeg', '.png', '.webp']
    for c in candidates:
        for e in exts:
            p = LOCAL_IMAGE_DIR / (c + e)
            if p.exists():
                return p
    return None

def download_image_to_temp(url):
    """Download image from URL to a NamedTemporaryFile and return file-like object or None."""
    try:
        resp = urllib.request.urlopen(url, timeout=10)
        tmp = NamedTemporaryFile(delete=True)
        tmp.write(resp.read())
        tmp.flush()
        return tmp
    except (URLError, ValueError, Exception):
        return None

print(f"Processing {len(products_df)} CSV rows (unique={args.unique})")

# Import products
created_count = 0
for _, row in products_df.iterrows():
    product_name = row['name']
    product_type = row.get('type', '')
    product_price = float(row['price']) if not pd.isna(row['price']) else 0.0

    # Map category
    category = category_map.get(product_type, 'Main')
    pretty_name = product_name.replace('_', ' ').title()

    # Check if product already exists (unless duplicates are allowed)
    exists = Product.objects.filter(name=pretty_name).exists()
    if exists and not args.allow_duplicates:
        print(f"- Skipped: {pretty_name} (already exists)")
        continue

    # Create product record
    product = Product.objects.create(
        name=pretty_name,
        price=product_price,
        category=category
    )

    # Attach image from CSV url if present
    image_attached = False
    if 'image_url' in df.columns:
        # find the row(s) that match this name in CSV (first match)
        matches = df[df['name'] == product_name]
        if not matches.empty:
            url = matches.iloc[0].get('image_url')
            if isinstance(url, str) and url.strip():
                tmp = download_image_to_temp(url.strip())
                if tmp:
                    filename = os.path.basename(url.split('?')[0]) or f"{product.id}.jpg"
                    with open(tmp.name, 'rb') as tmpf:
                        product.image.save(filename, File(tmpf))
                    image_attached = True

    # If not attached from URL, try local folder
    if not image_attached:
        local = find_local_image(product_name)
        if local:
            with open(local, 'rb') as f:
                product.image.save(local.name, File(f))
            image_attached = True

    # Create inventory entry with unique SKU
    sku = f"PIZZA-{uuid.uuid4().hex[:8].upper()}"
    InventoryItem.objects.create(
        product=product,
        sku=sku,
        quantity=50,  # Default stock
        reorder_point=10
    )

    created_count += 1
    print(f"✓ Created: {product.name} (₱{product_price:.2f}) - {category}{' [image]' if image_attached else ''}")

print(f"\n{created_count} products imported successfully!")
