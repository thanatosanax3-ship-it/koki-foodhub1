import os
import django
from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from io import BytesIO

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import make_password
from core.models import Product

# Create or get test user with proper password using fast hasher for testing
test_password = make_password('testpass123', hasher='default')
test_user, created = User.objects.get_or_create(
    username='testuser_modal', 
    defaults={'is_staff': True, 'password': test_password}
)
if not created:
    # Update password if user already exists
    test_user.password = test_password
    test_user.save()

# Ensure user is in Admin group
admin_group, _ = Group.objects.get_or_create(name='Admin')
test_user.groups.add(admin_group)

# Create a test image
img = Image.new('RGB', (100, 100), color='blue')
img_io = BytesIO()
img.save(img_io, 'JPEG')
img_io.seek(0)

# Simulate form submission like the modal does
client = Client()
login_success = client.login(username='testuser_modal', password='testpass123')
print(f"Login successful: {login_success}")

# Now submit the form with image
img_io.seek(0)  # Reset position
test_image = SimpleUploadedFile(
    name='modal_test_product.jpg',
    content=img_io.getvalue(),
    content_type='image/jpeg'
)

response = client.post('/products/create/', {
    'name': 'Modal Test Product',
    'category': 'Main',
    'price': '49.99',
    'size': 'M',
}, files={'image': test_image})

print(f"Response status: {response.status_code}")
print(f"Response URL: {response.url if hasattr(response, 'url') else 'N/A'}")

# Check if product was created
try:
    product = Product.objects.get(name='Modal Test Product')
    print(f"\n✓ Product created successfully!")
    print(f"  - Name: {product.name}")
    print(f"  - Category: {product.category}")
    print(f"  - Price: {product.price}")
    print(f"  - Image field: {product.image}")
    print(f"  - Image URL: {product.image.url if product.image else 'EMPTY - IMAGE NOT SAVED!'}")
    
    if product.image:
        print(f"  - File exists: {product.image.storage.exists(product.image.name)}")
except Product.DoesNotExist:
    print("\n✗ Product not created!")
except Exception as e:
    print(f"\n✗ Error: {e}")


# Try to create a product with image via POST
img_io.seek(0)
response = client.post('/products/create/', {
    'name': 'Modal Test Product',
    'size': 'M',
    'category': 'Main',
    'price': '50.00',
    'image': SimpleUploadedFile("modal_test.jpg", img_io.getvalue(), content_type="image/jpeg")
})

print(f"Response status: {response.status_code}")
print(f"Response redirect: {response.url if hasattr(response, 'url') else 'No redirect'}")

# Check if product was created
from core.models import Product
p = Product.objects.filter(name='Modal Test Product').first()
if p:
    print(f"Product created: {p.id} - {p.name}")
    print(f"Image: {p.image.url if p.image else 'NO IMAGE'}")
else:
    print("Product NOT created")
