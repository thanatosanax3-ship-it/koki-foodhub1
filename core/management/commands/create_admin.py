"""
Create additional admin/superuser account
Usage: python manage.py create_admin --username=joanna --email=joanna@example.com --password=YourPassword123
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Create a new admin/superuser account'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, required=True, help='Username for the admin account')
        parser.add_argument('--email', type=str, required=True, help='Email for the admin account')
        parser.add_argument('--password', type=str, required=True, help='Password for the admin account')

    def handle(self, *args, **options):
        User = get_user_model()
        username = options['username']
        email = options['email']
        password = options['password']

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'⚠️ User "{username}" already exists'))
            return

        try:
            user = User.objects.create_superuser(username, email, password)
            self.stdout.write(self.style.SUCCESS(f'✅ Admin account created successfully!'))
            self.stdout.write(f'   Username: {username}')
            self.stdout.write(f'   Email: {email}')
            self.stdout.write(f'   Password: {password}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error creating admin: {e}'))
