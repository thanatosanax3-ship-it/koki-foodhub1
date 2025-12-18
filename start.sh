#!/bin/bash
set -e

echo "=========================================="
echo "🚀 RENDER DEPLOYMENT INITIALIZATION"
echo "=========================================="

# Change to project directory  
cd /opt/render/project/src

# Run migrations with explicit verbose output
echo ""
echo "→ Running migrations..."
python manage.py migrate --verbosity 2

# Create admin user
echo ""
echo "→ Checking/creating admin user..."
python << END
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

admin_user = User.objects.filter(username='admin').first()
if admin_user:
    print("✅ Admin user already exists")
else:
    password = os.getenv('ADMIN_PASSWORD', 'admin123')
    email = os.getenv('ADMIN_EMAIL', 'admin@koki-foodhub.com')
    User.objects.create_superuser('admin', email, password)
    print("✅ Admin user created!")

print(f"📊 Total users in database: {User.objects.count()}")
END

echo ""
echo "=========================================="
echo "✅ INITIALIZATION COMPLETE"
echo "=========================================="
echo ""

# Start gunicorn
exec gunicorn \
    --bind 0.0.0.0:${PORT:-10000} \
    --workers 2 \
    --worker-class sync \
    --timeout 60 \
    --access-logfile - \
    --error-logfile - \
    koki_foodhub.wsgi:application
