from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from core.models import Product, InventoryItem, Sale


class Command(BaseCommand):
    help = "Create default roles and assign permissions"

    def handle(self, *args, **kwargs):
        product_ct = ContentType.objects.get_for_model(Product)
        inventory_ct = ContentType.objects.get_for_model(InventoryItem)
        sale_ct = ContentType.objects.get_for_model(Sale)

        # Admin: full permissions on Product, Inventory, Sales
        admin, _ = Group.objects.get_or_create(name="Admin")
        admin_perms = list(Permission.objects.filter(content_type=product_ct)) + \
                      list(Permission.objects.filter(content_type=inventory_ct)) + \
                      list(Permission.objects.filter(content_type=sale_ct))
        admin.permissions.set(admin_perms)

        # Cashier: no object-level permissions — only access to dashboard (handled by view decorators)
        cashier, _ = Group.objects.get_or_create(name="Cashier")
        cashier.permissions.clear()

        self.stdout.write(self.style.SUCCESS("Roles seeded: Admin, Cashier"))
