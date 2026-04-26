"""
Management command to create fake stock prediction questions
Run: python manage.py create_stock_questions
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random
import math
from users.models import StockPredictionQuestion


class Command(BaseCommand):
    help = 'Creates fake stock prediction questions with real stock names'

    def handle(self, *args, **options):
        self.stdout.write('Creating stock prediction questions...')
        
        # Real stock names with fake data
        questions_data = [
            {
                'stock_name': 'Apple Inc.',
                'stock_symbol': 'AAPL',
                'question': 'Based on the chart above, how do you think Apple stock will perform in the next week?',
                'expected_direction': 'up',
                'expected_keywords': ['up', 'rise', 'increase', 'bullish', 'grow'],
                'explanation': 'The chart shows a strong upward trend with price above both moving averages, indicating bullish momentum.',
                'hint': 'Prices are consistently making higher highs. Notice how the MA20 is providing support on every dip.',
                'difficulty': 'beginner',
                'base_score': 10,
                'max_score': 20,
            },
            {
                'stock_name': 'Tesla Inc.',
                'stock_symbol': 'TSLA',
                'question': 'Analyze the sudden volume spike and price rejection at the upper Bollinger Band.',
                'expected_direction': 'down',
                'expected_keywords': ['rejection', 'down', 'overbought', 'bearish', 'correction'],
                'explanation': 'A clear Shooting Star candle at a multi-month resistance level suggests a trend reversal.',
                'hint': 'Look at the long upper wick on the last candle. That usually signifies aggressive selling pressure at high prices.',
                'difficulty': 'intermediate',
                'base_score': 30,
                'max_score': 60,
            },
            {
                'stock_name': 'NVIDIA Corporation',
                'stock_symbol': 'NVDA',
                'question': 'Identify the pattern forming at the peak. Is this a healthy consolidation or a bearish reversal?',
                'expected_direction': 'down',
                'expected_keywords': ['double top', 'reversal', 'down', 'bearish', 'support'],
                'explanation': 'This is a textbook Double Top pattern with declining RSI, indicating weakening momentum at the peak.',
                'hint': 'Price tried twice to break the recent high but failed both times on lower volume. This is often a sign of exhaustion.',
                'difficulty': 'advanced',
                'base_score': 50,
                'max_score': 100,
            },
            {
                'stock_name': 'Reliance Industries',
                'stock_symbol': 'RELIANCE',
                'question': 'The stock is approaching a massive horizontal support zone. How do you play this?',
                'expected_direction': 'up',
                'expected_keywords': ['support', 'bounce', 'demand', 'up', 'accumulation'],
                'explanation': 'Price has historically bounced from this level 3 times. Accumulation volume is increasing.',
                'hint': 'Horizontal support zones usually act as psychological floors. Look for a Hammer candle or bullish engulfing pattern here.',
                'difficulty': 'intermediate',
                'base_score': 25,
                'max_score': 50,
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for q_data in questions_data:
            # Generate fake chart data (60 days)
            chart_data = []
            base_price = random.uniform(50, 500)
            current_price = base_price
            
            # Generate price history based on expected direction
            for i in range(60, -1, -1):
                date = (timezone.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                
                # Apply trend based on expected direction
                if q_data['expected_direction'] == 'up':
                    trend_factor = 1 + (0.001 * (60 - i))  # Gradual upward
                    volatility = random.gauss(0, 0.02)
                elif q_data['expected_direction'] == 'down':
                    trend_factor = 1 - (0.001 * (60 - i))  # Gradual downward
                    volatility = random.gauss(0, 0.02)
                else:  # neutral
                    trend_factor = 1.0
                    volatility = random.gauss(0, 0.015)  # Less volatility
                
                current_price = base_price * trend_factor * (1 + volatility)
                current_price = max(base_price * 0.7, min(base_price * 1.3, current_price))
                
                # Calculate moving averages
                ma20 = None
                ma50 = None
                if len(chart_data) >= 19:
                    recent_prices = [p['price'] for p in chart_data[-19:]] + [current_price]
                    ma20 = sum(recent_prices) / len(recent_prices)
                if len(chart_data) >= 49:
                    recent_prices = [p['price'] for p in chart_data[-49:]] + [current_price]
                    ma50 = sum(recent_prices) / len(recent_prices)
                
                chart_data.append({
                    'date': date,
                    'price': round(current_price, 2),
                    'volume': random.randint(1000000, 10000000),
                    'open': round(current_price * random.uniform(0.98, 1.02), 2),
                    'high': round(current_price * random.uniform(1.0, 1.03), 2),
                    'low': round(current_price * random.uniform(0.97, 1.0), 2),
                    'close': round(current_price, 2),
                    'ma20': round(ma20, 2) if ma20 else None,
                    'ma50': round(ma50, 2) if ma50 else None,
                })
            
            # Create or update question
            question, created = StockPredictionQuestion.objects.update_or_create(
                stock_symbol=q_data['stock_symbol'],
                defaults={
                    'stock_name': q_data['stock_name'],
                    'question': q_data['question'],
                    'chart_data': chart_data,
                    'expected_direction': q_data['expected_direction'],
                    'expected_keywords': q_data['expected_keywords'],
                    'explanation': q_data['explanation'],
                    'difficulty': q_data['difficulty'],
                    'base_score': q_data['base_score'],
                    'max_score': q_data['max_score'],
                    'is_active': True,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created {question.stock_symbol}: {question.stock_name}'))
            else:
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ Updated {question.stock_symbol}: {question.stock_name}'))
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Stock Prediction Questions Created!\n'
            f'  Created: {created_count}\n'
            f'  Updated: {updated_count}\n'
            f'  Total: {StockPredictionQuestion.objects.filter(is_active=True).count()} active questions'
        ))

