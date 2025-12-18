from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User, Group
import getpass


class Command(BaseCommand):
    help = 'Create a Cashier user and assign them to the Cashier group'

    def add_arguments(self, parser):
        parser.add_argument('username', nargs='?', help='Username for the new cashier')
        parser.add_argument('email', nargs='?', help='Email for the new cashier')
        parser.add_argument('password', nargs='?', help='Password for the new cashier')

    def handle(self, *args, **options):
        username = options.get('username')
        email = options.get('email')
        password = options.get('password')

        # Prompt interactively if not provided
        if not username:
            username = input('Username: ').strip()
        if not email:
            email = input('Email: ').strip()
        if not password:
            # Use getpass to avoid echoing
            while True:
                pw = getpass.getpass('Password: ')
                pw2 = getpass.getpass('Password (again): ')
                if pw != pw2:
                    self.stderr.write(self.style.ERROR('Passwords do not match. Try again.'))
                    continue
                if len(pw) < 6:
                    self.stderr.write(self.style.ERROR('Password must be at least 6 characters.'))
                    continue
                password = pw
                break

        # Basic validation
        if not username:
            raise CommandError('Username is required')
        if not email:
            raise CommandError('Email is required')

        # See if user exists
        if User.objects.filter(username=username).exists():
            self.stderr.write(self.style.ERROR(f"User '{username}' already exists."))
            return

        # Create user
        user = User.objects.create_user(username=username, email=email, password=password)
        user.is_active = True
        user.save()

        # Ensure Cashier group exists and add
        cashier_group, _ = Group.objects.get_or_create(name='Cashier')
        user.groups.add(cashier_group)

        self.stdout.write(self.style.SUCCESS(f"Created cashier user '{username}' and added to 'Cashier' group."))