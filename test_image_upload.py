import os
import django
from django.core.files.uploadedfile import SimpleUploadedFile

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from core.models import Product
from PIL import Image
from io import BytesIO

# Create a test image in memory
img = Image.new('RGB', (100, 100), color='red')
img_io = BytesIO()
img.save(img_io, 'JPEG')
img_io.seek(0)

# Create a product with the image
product = Product.objects.create(
    name='Test Product with Image',
    category='Main',
    price=50.00,
    image=SimpleUploadedFile("test_image.jpg", img_io.getvalue(), content_type="image/jpeg")
)

print(f"Created product: {product.id} - {product.name}")
print(f"Image path: {product.image.url if product.image else 'No image'}")
print(f"Image file exists: {os.path.exists(product.image.path) if product.image else 'N/A'}")
