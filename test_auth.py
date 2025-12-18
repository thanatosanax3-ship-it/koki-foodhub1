import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate

# Check users
print("=== Users in database ===")
users = User.objects.all()
print(f"Total users: {users.count()}")
for u in users:
    print(f"  - Username: {u.username}, Superuser: {u.is_superuser}, Staff: {u.is_staff}, Active: {u.is_active}")

# Test login
print("\n=== Testing login ===")
user = authenticate(username='admin', password='admin123')
if user is not None:
    print(f"✓ Login successful: {user.username}")
else:
    print("✗ Login failed with admin/admin123")
    # Try to get the user and check if password is set
    try:
        admin_user = User.objects.get(username='admin')
        print(f"User exists: {admin_user.username}")
        print(f"Password hash: {admin_user.password[:50]}...")
        print(f"Password check: {admin_user.check_password('admin123')}")
    except User.DoesNotExist:
        print("Admin user does not exist!")
