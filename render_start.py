#!/usr/bin/env python
"""
Render deployment startup script
Runs migrations and starts the app
"""
import os
import sys
import subprocess
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')

print("\n" + "="*60)
print("🚀 RENDER DEPLOYMENT - STARTING UP")
print("="*60)

# Run migrations
print("\n→ Running database migrations...")
result = subprocess.run([sys.executable, 'manage.py', 'migrate', '--verbosity', '2'], 
                       capture_output=False, text=True)
if result.returncode != 0:
    print("⚠️  Migration warning (continuing anyway)")

# Initialize Django
django.setup()

# Create admin user
print("\n→ Creating admin user...")
from django.contrib.auth import get_user_model
User = get_user_model()

try:
    admin = User.objects.get(username='admin')
    print("✅ Admin user already exists")
except User.DoesNotExist:
    password = os.getenv('ADMIN_PASSWORD', 'admin123')
    email = os.getenv('ADMIN_EMAIL', 'admin@koki-foodhub.com')
    User.objects.create_superuser('admin', email, password)
    print(f"✅ Admin user created (username: admin)")

print(f"📊 Total users: {User.objects.count()}")

print("\n" + "="*60)
print("✅ INITIALIZATION COMPLETE")
print("="*60 + "\n")

# Start gunicorn
print("→ Starting Gunicorn web server...\n")
os.execvp('gunicorn', [
    'gunicorn',
    '--bind', f'0.0.0.0:{os.getenv("PORT", "10000")}',
    '--workers', '2',
    '--worker-class', 'sync',
    '--timeout', '60',
    '--access-logfile', '-',
    '--error-logfile', '-',
    'koki_foodhub.wsgi:application'
])
