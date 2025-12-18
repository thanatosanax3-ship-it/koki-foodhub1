import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from core.models import Product
from django.db.models.functions import Lower

qs = Product.objects.all().order_by(Lower('name'))
print('First 30 product names (case-insensitive A→Z):')
for p in qs[:30]:
    print(p.name)
