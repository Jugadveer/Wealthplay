"""
Management command to create 16 custom stocks with different behavior patterns
Run: python manage.py create_custom_stocks
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random
import math
from users.models import CustomStock


class Command(BaseCommand):
    help = 'Creates 16 custom stocks with different behavior patterns'

    def handle(self, *args, **options):
        self.stdout.write('Creating custom stocks...')
        
        stocks_data = [
            # Penny Stocks (Low price, high volatility)
            {
                'symbol': 'PENNY1',
                'name': 'Penny Tech Corp',
                'base_price': 5.50,
                'stock_type': 'penny',
                'sector': 'Technology',
                'category': 'Penny Stock',
                'volatility': 0.08,  # 8% daily volatility
                'trend': 'bullish',
                'trend_strength': 0.3,
            },
            {
                'symbol': 'PENNY2',
                'name': 'Micro Finance Ltd',
                'base_price': 3.25,
                'stock_type': 'penny',
                'sector': 'Finance',
                'category': 'Penny Stock',
                'volatility': 0.10,  # 10% daily volatility
                'trend': 'bearish',
                'trend_strength': 0.2,
            },
            
            # Highly Volatile Stocks
            {
                'symbol': 'VOLT1',
                'name': 'Volatile Energy Inc',
                'base_price': 125.00,
                'stock_type': 'volatile',
                'sector': 'Energy',
                'category': 'High Volatility',
                'volatility': 0.06,  # 6% daily volatility
                'trend': 'bullish',
                'trend_strength': 0.5,
            },
            {
                'symbol': 'VOLT2',
                'name': 'Crypto Mining Co',
                'base_price': 85.50,
                'stock_type': 'volatile',
                'sector': 'Technology',
                'category': 'High Volatility',
                'volatility': 0.07,  # 7% daily volatility
                'trend': 'neutral',
                'trend_strength': 0.0,
            },
            
            # Stable Blue Chips
            {
                'symbol': 'BLUE1',
                'name': 'Stable Bank Ltd',
                'base_price': 450.00,
                'stock_type': 'stable',
                'sector': 'Finance',
                'category': 'Large Cap',
                'volatility': 0.015,  # 1.5% daily volatility
                'trend': 'bullish',
                'trend_strength': 0.2,
            },
            {
                'symbol': 'BLUE2',
                'name': 'Reliable Utilities',
                'base_price': 320.00,
                'stock_type': 'stable',
                'sector': 'Utilities',
                'category': 'Large Cap',
                'volatility': 0.012,  # 1.2% daily volatility
                'trend': 'neutral',
                'trend_strength': 0.1,
            },
            
            # Growth Stocks
            {
                'symbol': 'GROW1',
                'name': 'Growth Tech Solutions',
                'base_price': 250.00,
                'stock_type': 'growth',
                'sector': 'Technology',
                'category': 'Mid Cap',
                'volatility': 0.04,  # 4% daily volatility
                'trend': 'bullish',
                'trend_strength': 0.6,
            },
            {
                'symbol': 'GROW2',
                'name': 'Emerging Pharma',
                'base_price': 180.00,
                'stock_type': 'growth',
                'sector': 'Healthcare',
                'category': 'Mid Cap',
                'volatility': 0.035,  # 3.5% daily volatility
                'trend': 'bullish',
                'trend_strength': 0.4,
            },
            
            # Dividend Stocks
            {
                'symbol': 'DIV1',
                'name': 'Dividend Power Corp',
                'base_price': 550.00,
                'stock_type': 'dividend',
                'sector': 'Finance',
                'category': 'Large Cap',
                'volatility': 0.02,  # 2% daily volatility
                'trend': 'bullish',
                'trend_strength': 0.15,
            },
            {
                'symbol': 'DIV2',
                'name': 'Steady Income Ltd',
                'base_price': 425.00,
                'stock_type': 'dividend',
                'sector': 'Real Estate',
                'category': 'Large Cap',
                'volatility': 0.018,  # 1.8% daily volatility
                'trend': 'neutral',
                'trend_strength': 0.1,
            },
            
            # Tech Stocks
            {
                'symbol': 'TECH1',
                'name': 'AI Innovations Ltd',
                'base_price': 750.00,
                'stock_type': 'tech',
                'sector': 'Technology',
                'category': 'Large Cap',
                'volatility': 0.045,  # 4.5% daily volatility
                'trend': 'bullish',
                'trend_strength': 0.7,
            },
            {
                'symbol': 'TECH2',
                'name': 'Cloud Services Inc',
                'base_price': 380.00,
                'stock_type': 'tech',
                'sector': 'Technology',
                'category': 'Mid Cap',
                'volatility': 0.038,  # 3.8% daily volatility
                'trend': 'bullish',
                'trend_strength': 0.5,
            },
            
            # Finance Stocks
            {
                'symbol': 'FIN1',
                'name': 'Investment Bank Ltd',
                'base_price': 650.00,
                'stock_type': 'finance',
                'sector': 'Finance',
                'category': 'Large Cap',
                'volatility': 0.03,  # 3% daily volatility
                'trend': 'bullish',
                'trend_strength': 0.3,
            },
            {
                'symbol': 'FIN2',
                'name': 'Credit Union Corp',
                'base_price': 280.00,
                'stock_type': 'finance',
                'sector': 'Finance',
                'category': 'Mid Cap',
                'volatility': 0.025,  # 2.5% daily volatility
                'trend': 'neutral',
                'trend_strength': 0.1,
            },
            
            # Energy Stocks
            {
                'symbol': 'ENER1',
                'name': 'Green Energy Co',
                'base_price': 195.00,
                'stock_type': 'energy',
                'sector': 'Energy',
                'category': 'Mid Cap',
                'volatility': 0.05,  # 5% daily volatility
                'trend': 'bullish',
                'trend_strength': 0.4,
            },
            {
                'symbol': 'ENER2',
                'name': 'Oil & Gas Ltd',
                'base_price': 145.00,
                'stock_type': 'energy',
                'sector': 'Energy',
                'category': 'Mid Cap',
                'volatility': 0.055,  # 5.5% daily volatility
                'trend': 'bearish',
                'trend_strength': 0.3,
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for stock_data in stocks_data:
            # Generate price history (60 days)
            price_history = []
            current_price = float(stock_data['base_price'])
            base_price = current_price
            
            # Calculate market cap
            market_cap_value = base_price * random.randint(1000000, 50000000)
            if market_cap_value < 500000000:
                market_cap = f"₹{market_cap_value/10000000:.1f} Cr"
            else:
                market_cap = f"₹{market_cap_value/100000000:.1f} B"
            
            # Generate historical prices
            for i in range(60, -1, -1):
                date = (timezone.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                
                # Apply trend
                if stock_data['trend'] == 'bullish':
                    trend_factor = 1 + (stock_data['trend_strength'] * 0.0001 * (60 - i))
                elif stock_data['trend'] == 'bearish':
                    trend_factor = 1 - (stock_data['trend_strength'] * 0.0001 * (60 - i))
                else:
                    trend_factor = 1.0
                
                # Apply random volatility
                volatility_change = random.gauss(0, stock_data['volatility'])
                current_price = base_price * trend_factor * (1 + volatility_change)
                
                # Ensure price doesn't go negative or too extreme
                current_price = max(base_price * 0.5, min(base_price * 2.0, current_price))
                
                # Calculate moving averages
                ma20 = None
                ma50 = None
                if len(price_history) >= 19:
                    recent_prices = [p['price'] for p in price_history[-19:]] + [current_price]
                    ma20 = sum(recent_prices) / len(recent_prices)
                if len(price_history) >= 49:
                    recent_prices = [p['price'] for p in price_history[-49:]] + [current_price]
                    ma50 = sum(recent_prices) / len(recent_prices)
                
                price_history.append({
                    'date': date,
                    'price': round(current_price, 2),
                    'volume': random.randint(100000, 10000000),
                    'open': round(current_price * random.uniform(0.98, 1.02), 2),
                    'high': round(current_price * random.uniform(1.0, 1.03), 2),
                    'low': round(current_price * random.uniform(0.97, 1.0), 2),
                    'close': round(current_price, 2),
                    'ma20': round(ma20, 2) if ma20 else None,
                    'ma50': round(ma50, 2) if ma50 else None,
                })
            
            # Calculate current change percent
            if len(price_history) >= 2:
                prev_price = price_history[-2]['price']
                current_price = price_history[-1]['price']
                change_percent = ((current_price - prev_price) / prev_price) * 100
            else:
                change_percent = 0.0
            
            # Create or update stock
            stock, created = CustomStock.objects.update_or_create(
                symbol=stock_data['symbol'],
                defaults={
                    'name': stock_data['name'],
                    'base_price': stock_data['base_price'],
                    'current_price': round(current_price, 2),
                    'change_percent': round(change_percent, 2),
                    'stock_type': stock_data['stock_type'],
                    'sector': stock_data['sector'],
                    'category': stock_data['category'],
                    'volatility': stock_data['volatility'],
                    'trend': stock_data['trend'],
                    'trend_strength': stock_data['trend_strength'],
                    'price_history': price_history,
                    'currency': 'INR',
                    'market_cap': market_cap,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created {stock.symbol}: {stock.name} - ₹{stock.current_price}'))
            else:
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ Updated {stock.symbol}: {stock.name} - ₹{stock.current_price}'))
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Custom Stocks Created!\n'
            f'  Created: {created_count}\n'
            f'  Updated: {updated_count}\n'
            f'  Total: {CustomStock.objects.count()} custom stocks'
        ))

