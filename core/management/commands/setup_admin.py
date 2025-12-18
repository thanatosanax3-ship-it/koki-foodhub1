from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

User = get_user_model()

class Command(BaseCommand):
    help = 'Create admin user for Render deployment'

    def handle(self, *args, **options):
        username = 'admin'
        password = os.getenv('ADMIN_PASSWORD', 'admin123')
        email = os.getenv('ADMIN_EMAIL', 'admin@koki-foodhub.com')
        
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            user.set_password(password)
            user.save()
            self.stdout.write(f"✅ Admin user updated")
        else:
            User.objects.create_superuser(username, email, password)
            self.stdout.write(f"✅ Admin user created")
        
        self.stdout.write(f"📊 Total users: {User.objects.count()}")
