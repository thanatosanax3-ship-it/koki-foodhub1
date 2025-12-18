from django.core.management.base import BaseCommand
from core.models import Product, Sale
from core.services.csv_forecasting import load_csv_data
from django.utils import timezone
import os

class Command(BaseCommand):
    help = 'Import sales data from CSV file (limited to N records)'

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
            help='Limit number of sales to import',
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
        
        # Group by product name and count units sold
        product_sales = {}
        for _, row in df.iterrows():
            product_name = row['name']
            date = row['date']
            price = float(row['price'])
            
            if product_name not in product_sales:
                product_sales[product_name] = []
            
            product_sales[product_name].append({
                'date': date,
                'price': price
            })
        
        # Import sales
        self.stdout.write(
            self.style.SUCCESS(f'\nImporting up to {limit} sales records...')
        )
        
        imported_count = 0
        skipped_count = 0
        
        # Get or create products and add sales
        for product_name, sales_data in product_sales.items():
            if imported_count >= limit:
                break
            
            # Get or create product
            product, created = Product.objects.get_or_create(
                name=product_name,
                defaults={
                    'category': 'Pizza',
                    'price': sales_data[0]['price'],
                    'is_active': True
                }
            )
            
            # Add sales for this product (up to limit)
            for sale_info in sales_data:
                if imported_count >= limit:
                    break
                
                # Count how many times this product was sold in same transaction
                # For simplicity, each row = 1 unit sold
                try:
                    sale = Sale.objects.create(
                        product=product,
                        date=sale_info['date'],
                        units_sold=1,
                        revenue=sale_info['price']
                    )
                    imported_count += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'Error creating sale for {product_name}: {e}')
                    )
                    skipped_count += 1
        
        # Display results
        self.stdout.write(
            self.style.SUCCESS(f'\nSuccessfully imported {imported_count} sales records!')
        )
        if skipped_count > 0:
            self.stdout.write(
                self.style.WARNING(f'Skipped {skipped_count} records due to errors')
            )
        
        # Show summary
        total_sales = Sale.objects.count()
        total_revenue = sum(s.revenue for s in Sale.objects.all())
        
        self.stdout.write(
            self.style.SUCCESS(f'\nDatabase Summary:')
        )
        self.stdout.write(f'  Total Sales Records: {total_sales}')
        self.stdout.write(f'  Total Revenue: ${total_revenue:.2f}')
        self.stdout.write(f'  Total Products: {Product.objects.count()}')
