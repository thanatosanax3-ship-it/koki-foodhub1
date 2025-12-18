from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Product, Sale
from core.services.csv_forecasting import get_csv_forecast
from datetime import timedelta

class Command(BaseCommand):
    help = 'Generate 30-day sales forecast for all products'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv',
            type=str,
            help='Path to CSV file',
            default='pizzaplace.csv'
        )
        parser.add_argument(
            '--days',
            type=int,
            help='Number of days to forecast',
            default=30
        )

    def handle(self, *args, **options):
        csv_path = options['csv']
        forecast_days = options['days']
        
        self.stdout.write(
            self.style.SUCCESS(f'Generating {forecast_days}-day sales forecast...')
        )
        
        # Get forecasts for all products
        forecasts = get_csv_forecast(csv_path)
        
        if not forecasts:
            self.stdout.write(
                self.style.ERROR('No forecast data available')
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS(f'Generated forecasts for {len(forecasts)} products\n')
        )
        
        # Calculate 30-day forecast
        today = timezone.now().date()
        total_daily_forecast = 0
        total_30day_forecast = 0
        
        # Summary by product
        self.stdout.write(
            self.style.SUCCESS('=== 30-DAY FORECAST SUMMARY ===\n')
        )
        
        product_forecasts = []
        
        for product_name, forecast_data in sorted(forecasts.items()):
            daily_forecast = forecast_data['forecast']
            forecast_30days = daily_forecast * forecast_days
            total_daily_forecast += daily_forecast
            total_30day_forecast += forecast_30days
            
            trend = forecast_data['trend']
            confidence = forecast_data['confidence']
            
            product_forecasts.append({
                'name': product_name,
                'daily': daily_forecast,
                '30day': forecast_30days,
                'trend': trend,
                'confidence': confidence,
                'avg': forecast_data['avg'],
                'last_7_days': forecast_data['last_7_days']
            })
            
            self.stdout.write(
                f"{product_name}:"
            )
            self.stdout.write(
                f"  Daily Forecast: {daily_forecast} units"
            )
            self.stdout.write(
                f"  30-Day Total: {forecast_30days} units"
            )
            self.stdout.write(
                f"  Trend: {trend.upper()}"
            )
            self.stdout.write(
                f"  Confidence: {confidence:.1f}%"
            )
            self.stdout.write(f"")
        
        # Overall forecast
        self.stdout.write(
            self.style.SUCCESS('=== OVERALL FORECAST ===\n')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Daily Average: {total_daily_forecast} units')
        )
        self.stdout.write(
            self.style.SUCCESS(f'30-Day Total: {total_30day_forecast} units')
        )
        
        # Average confidence
        avg_confidence = sum(p['confidence'] for p in product_forecasts) / len(product_forecasts) if product_forecasts else 0
        self.stdout.write(
            self.style.SUCCESS(f'Forecast Confidence: {avg_confidence:.1f}%\n')
        )
        
        # Forecast breakdown by week
        self.stdout.write(
            self.style.SUCCESS('=== WEEKLY BREAKDOWN ===\n')
        )
        
        for week in range(1, 5):
            week_start = today + timedelta(days=(week-1)*7)
            week_total = total_daily_forecast * 7
            self.stdout.write(
                f"Week {week} ({week_start.strftime('%b %d')}): {week_total} units"
            )
        
        # Top performing products
        self.stdout.write(
            self.style.SUCCESS('\n=== TOP 5 PREDICTED PRODUCTS (30 DAYS) ===\n')
        )
        
        top_products = sorted(product_forecasts, key=lambda x: x['30day'], reverse=True)[:5]
        for i, product in enumerate(top_products, 1):
            self.stdout.write(
                f"{i}. {product['name']}: {product['30day']} units (Daily: {product['daily']})"
            )
        
        # Products needing attention (low stock prediction)
        self.stdout.write(
            self.style.SUCCESS('\n=== PRODUCTS WITH INCREASING TREND ===\n')
        )
        
        increasing = [p for p in product_forecasts if p['trend'] == 'increasing']
        if increasing:
            for product in increasing[:5]:
                self.stdout.write(
                    f"📈 {product['name']}: +Increasing (Confidence: {product['confidence']:.1f}%)"
                )
        else:
            self.stdout.write('No products with increasing trend detected.')
        
        # Products with low confidence
        self.stdout.write(
            self.style.SUCCESS('\n=== MONITORING REQUIRED ===\n')
        )
        
        low_confidence = [p for p in product_forecasts if p['confidence'] < 30]
        if low_confidence:
            self.stdout.write(
                self.style.WARNING(f'Products with low confidence (<30%):')
            )
            for product in low_confidence[:5]:
                self.stdout.write(
                    f"⚠️  {product['name']}: Confidence {product['confidence']:.1f}%"
                )
        else:
            self.stdout.write(
                self.style.SUCCESS('All products have good prediction confidence (≥30%)')
            )
        
        # Forecast period information
        forecast_end = today + timedelta(days=forecast_days)
        self.stdout.write(
            self.style.SUCCESS(f'\n=== FORECAST PERIOD ===')
        )
        self.stdout.write(
            f'Start Date: {today.strftime("%B %d, %Y")}'
        )
        self.stdout.write(
            f'End Date: {forecast_end.strftime("%B %d, %Y")}'
        )
        self.stdout.write(
            f'Total Days: {forecast_days}'
        )
        
        self.stdout.write(
            self.style.SUCCESS('\n✅ 30-Day forecast completed successfully!')
        )
