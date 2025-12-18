from django.core.management.base import BaseCommand
from core.models import Product, Sale
from core.services.csv_forecasting import load_csv_data
import os

class Command(BaseCommand):
    help = 'Import products from CSV that match existing sales records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv',
            type=str,
            help='Path to CSV file',
            default='pizzaplace.csv'
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of products to import',
            default=100
        )

    def handle(self, *args, **options):
        csv_path = options['csv']
        limit = options['limit']
        
        # Check if file exists
        if not os.path.exists(csv_path):
            self.stdout.write(
                self.style.ERROR(f'CSV file not found: {csv_path}')
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS(f'Loading data from {csv_path}...')
        )
        
        # Load CSV data
        df = load_csv_data(csv_path)
        if df is None:
            self.stdout.write(
                self.style.ERROR('Failed to load CSV data')
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS(f'Loaded {len(df)} records from CSV')
        )
        
        # Get product names that are already in sales
        sales_product_names = set(Sale.objects.values_list('product__name', flat=True))
        
        self.stdout.write(
            self.style.SUCCESS(f'Found {len(sales_product_names)} products in sales: {", ".join(sorted(sales_product_names))}')
        )
        
        # Get unique products from CSV and count occurrences
        product_stats = df.groupby('name').agg({
            'price': 'first',
            'type': 'first',
            'id': 'count'
        }).reset_index()
        product_stats.columns = ['name', 'price', 'type', 'count']
        product_stats = product_stats.sort_values('count', ascending=False)
        
        self.stdout.write(
            self.style.SUCCESS(f'Found {len(product_stats)} unique products in CSV')
        )
        
        # Filter to only products that match sales, then add others
        matching_products = []
        other_products = []
        
        for _, row in product_stats.iterrows():
            if row['name'] in sales_product_names:
                matching_products.append(row)
            else:
                other_products.append(row)
        
        self.stdout.write(
            self.style.SUCCESS(f'Matching products (in sales): {len(matching_products)}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Other products (not in sales): {len(other_products)}')
        )
        
        # Combine: first matching products, then others to reach limit
        products_to_import = matching_products + other_products
        products_to_import = products_to_import[:limit]
        
        # Import products
        self.stdout.write(
            self.style.SUCCESS(f'\nImporting up to {limit} products...')
        )
        
        imported_count = 0
        skipped_count = 0
        
        for product_data in products_to_import:
            product_name = product_data['name']
            price = float(product_data['price'])
            product_type = product_data['type']
            
            # Get or create product
            product, created = Product.objects.get_or_create(
                name=product_name,
                defaults={
                    'category': product_type,
                    'price': price,
                    'is_active': True
                }
            )
            
            if created:
                imported_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created: {product_name} - ${price:.2f} ({product_type})')
                )
            else:
                skipped_count += 1
        
        # Display results
        self.stdout.write(
            self.style.SUCCESS(f'\n=== Import Complete ===')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Created: {imported_count} new products')
        )
        if skipped_count > 0:
            self.stdout.write(
                self.style.WARNING(f'Skipped: {skipped_count} existing products')
            )
        
        # Show summary
        total_products = Product.objects.count()
        
        self.stdout.write(
            self.style.SUCCESS(f'\nDatabase Summary:')
        )
        self.stdout.write(f'  Total Products: {total_products}')
        self.stdout.write(f'  Total Sales Records: {Sale.objects.count()}')
        
        # Show products by category
        categories = Product.objects.values_list('category', flat=True).distinct()
        self.stdout.write(f'\n  Products by Category:')
        for category in sorted(categories):
            count = Product.objects.filter(category=category).count()
            self.stdout.write(f'    - {category}: {count} products')
