from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = 'Create default user groups (Admin, Cashier)'

    def handle(self, *args, **options):
        admin, created = Group.objects.get_or_create(name='Admin')
        cashier, created = Group.objects.get_or_create(name='Cashier')
        self.stdout.write(self.style.SUCCESS('✓ Groups created/verified: Admin, Cashier'))
