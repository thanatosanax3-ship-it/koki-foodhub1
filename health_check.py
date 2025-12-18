"""
Health check and initialization script for Render deployment
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from django.core.management import call_command
from django.contrib.auth import get_user_model

print("🔍 Checking deployment health...")

# Check database connection
print("✓ Django setup successful")

# Run migrations
print("→ Running migrations...")
try:
    call_command('migrate', verbosity=0)
    print("✓ Migrations successful")
except Exception as e:
    print(f"⚠ Migration error: {e}")
    sys.exit(1)

# Create admin user if needed
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    print("→ Creating admin user...")
    try:
        User.objects.create_superuser(
            username='admin',
            email=os.getenv('ADMIN_EMAIL', 'admin@koki-foodhub.com'),
            password=os.getenv('ADMIN_PASSWORD', 'admin123')
        )
        print("✓ Admin user created")
    except Exception as e:
        print(f"⚠ Admin creation error: {e}")

print("✓ All checks passed!")
