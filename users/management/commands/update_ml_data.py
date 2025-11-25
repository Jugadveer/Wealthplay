"""
Django management command to update cached stock data and ML predictions.

This command should be run periodically (e.g., every 5 minutes) via:
- Cron job (Linux/Mac)
- Task Scheduler (Windows)
- Celery Beat (recommended for production)

Usage:
    python manage.py update_ml_data
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import PredictedStockData
from users.ml_predictor import ML_PREDICTOR, TICKERS
from users.portfolio_views import get_stock_info, generate_price_history
import traceback


class Command(BaseCommand):
    help = 'Update cached stock data and ML predictions for all tickers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--symbol',
            type=str,
            help='Update a specific symbol only (optional)',
        )

    def handle(self, *args, **options):
        symbols_to_update = [options['symbol']] if options.get('symbol') else TICKERS
        
        self.stdout.write(f'Starting ML data update for {len(symbols_to_update)} symbols...')
        
        success_count = 0
        error_count = 0
        
        for symbol in symbols_to_update:
            try:
                self.stdout.write(f'Processing {symbol}...')
                
                # 1. Fetch live stock info (use_cache=False to get fresh data)
                stock_info = get_stock_info(symbol, use_cache=False)
                
                if stock_info.get('current_price', 0.0) <= 0.0:
                    self.stdout.write(self.style.WARNING(f'  Skipping {symbol}: No price data available'))
                    continue
                
                # 2. Generate price history (use_cache=False to get fresh data)
                price_history = generate_price_history(symbol, days=60, use_cache=False)
                
                # 3. Run ML prediction
                prediction_results = ML_PREDICTOR.predict(symbol)
                
                # 4. Create or update cached record
                from users.ml_predictor import NSE_TICKERS
                is_indian_stock = symbol.upper() in NSE_TICKERS
                cached_data, created = PredictedStockData.objects.update_or_create(
                    symbol=symbol,
                    defaults={
                        'name': stock_info.get('name', symbol),
                        'current_price': stock_info.get('current_price', 0.0),
                        'change_percent': stock_info.get('change_percent', 0.0),
                        'category': stock_info.get('category', 'Unknown'),
                        'sector': stock_info.get('sector', 'Unknown'),
                        'market_cap': stock_info.get('market_cap', 'N/A'),
                        'currency': 'INR' if is_indian_stock else 'USD',
                        'price_history': price_history,
                        'ml_direction': prediction_results.get('direction', 'neutral'),
                        'ml_confidence': prediction_results.get('confidence', 0.5),
                        'ml_regime': prediction_results.get('regime', 'Unknown'),
                        'ml_volatility': prediction_results.get('vol', 0.0),
                    }
                )
                
                action = 'Created' if created else 'Updated'
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ {action} {symbol}: ${stock_info.get("current_price", 0):.2f} - {prediction_results.get("direction", "neutral")}')
                )
                success_count += 1
                
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Error processing {symbol}: {str(e)}')
                )
                if options.get('verbosity', 1) >= 2:
                    self.stdout.write(traceback.format_exc())
        
        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Update complete: {success_count} successful, {error_count} errors'))
        
        if success_count > 0:
            self.stdout.write(f'Cached data is now available for instant API responses!')

