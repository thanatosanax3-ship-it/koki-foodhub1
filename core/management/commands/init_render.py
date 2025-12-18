"""
Initialize Render deployment: run migrations and create superuser if needed
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.management import call_command
import os
import sys


class Command(BaseCommand):
    help = 'Initialize Render deployment with migrations and default admin user'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Initializing Render deployment...')
        self.stdout.flush()

        # Run migrations
        self.stdout.write('📦 Running database migrations...')
        self.stdout.flush()
        try:
            call_command('migrate', verbosity=0)
            self.stdout.write(self.style.SUCCESS('✅ Migrations completed'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Migration error: {e}'))
            self.stdout.flush()

        # Create superuser if it doesn't exist
        try:
            User = get_user_model()
            admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
            
            if not User.objects.filter(username='admin').exists():
                self.stdout.write('👤 Creating admin user...')
                self.stdout.flush()
                
                User.objects.create_superuser(
                    username='admin',
                    email=os.getenv('ADMIN_EMAIL', 'admin@koki-foodhub.com'),
                    password=admin_password
                )
                self.stdout.write(self.style.SUCCESS('✅ Admin user created successfully!'))
                self.stdout.write(f'   Username: admin')
                self.stdout.write(f'   Password: {admin_password}')
            else:
                self.stdout.write(self.style.SUCCESS('ℹ️ Admin user already exists'))
            
            self.stdout.flush()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {e}'))
            self.stdout.write(self.style.WARNING('⚠️ Admin user creation failed - continuing anyway'))
            self.stdout.flush()

        self.stdout.write(self.style.SUCCESS('✅ Render initialization complete!'))
        self.stdout.flush()
