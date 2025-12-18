from django.core.management.base import BaseCommand
from core.services.csv_forecasting import load_csv_data, get_csv_forecast
import os

class Command(BaseCommand):
    help = 'Train forecasting model using CSV data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv',
            type=str,
            help='Path to CSV file',
            default='pizzaplace.csv'
        )

    def handle(self, *args, **options):
        csv_path = options['csv']
        
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
            self.style.SUCCESS(f'Loaded {len(df)} records')
        )
        
        # Train forecasting model
        self.stdout.write(
            self.style.SUCCESS('Training forecasting model...')
        )
        
        forecasts = get_csv_forecast(csv_path)
        
        if not forecasts:
            self.stdout.write(
                self.style.ERROR('No forecasts generated')
            )
            return
        
        # Display results
        self.stdout.write(
            self.style.SUCCESS(f'\nForecasting model trained successfully!')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Generated forecasts for {len(forecasts)} products\n')
        )
        
        # Print forecast details
        for product_name, forecast_data in sorted(forecasts.items()):
            self.stdout.write(
                f"\n{self.style.SUCCESS(product_name)}:"
            )
            self.stdout.write(
                f"  Forecast (next day): {forecast_data['forecast']} units"
            )
            self.stdout.write(
                f"  Trend: {forecast_data['trend']}"
            )
            self.stdout.write(
                f"  Confidence: {forecast_data['confidence']}"
            )
            self.stdout.write(
                f"  Last 7 days total: {forecast_data['last_7_days']} units"
            )
            self.stdout.write(
                f"  Daily average: {forecast_data['avg']:.1f} units"
            )
