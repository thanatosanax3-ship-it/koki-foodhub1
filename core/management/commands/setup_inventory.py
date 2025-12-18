from django.core.management.base import BaseCommand
from core.models import Product, InventoryItem

class Command(BaseCommand):
    help = 'Create inventory items for all products'

    def add_arguments(self, parser):
        parser.add_argument(
            '--quantity',
            type=int,
            help='Initial quantity for each product',
            default=50
        )
        parser.add_argument(
            '--reorder',
            type=int,
            help='Reorder point for each product',
            default=10
        )

    def handle(self, *args, **options):
        initial_qty = options['quantity']
        reorder_point = options['reorder']
        
        self.stdout.write(
            self.style.SUCCESS(f'Creating inventory items for all products...')
        )
        
        created_count = 0
        skipped_count = 0
        
        for product in Product.objects.all():
            sku = f"SKU-{product.id}-{product.name.upper()[:10]}"
            
            # Get or create inventory item
            inv, created = InventoryItem.objects.get_or_create(
                product=product,
                defaults={
                    'sku': sku,
                    'quantity': initial_qty,
                    'reorder_point': reorder_point
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created: {product.name} - SKU: {sku} - Qty: {initial_qty}')
                )
            else:
                skipped_count += 1
        
        # Display results
        self.stdout.write(
            self.style.SUCCESS(f'\n=== Inventory Setup Complete ===')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Created: {created_count} inventory items')
        )
        if skipped_count > 0:
            self.stdout.write(
                self.style.WARNING(f'Skipped: {skipped_count} existing items')
            )
        
        # Show summary
        total_inventory = InventoryItem.objects.count()
        total_quantity = sum(i.quantity for i in InventoryItem.objects.all())
        
        self.stdout.write(
            self.style.SUCCESS(f'\nDatabase Summary:')
        )
        self.stdout.write(f'  Total Inventory Items: {total_inventory}')
        self.stdout.write(f'  Total Stock Quantity: {total_quantity} units')
