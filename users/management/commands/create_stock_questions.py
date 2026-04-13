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
                'difficulty': 'easy',
                'base_score': 10,
                'max_score': 20,
            },
            {
                'stock_name': 'Microsoft Corporation',
                'stock_symbol': 'MSFT',
                'question': 'Looking at the price chart, what is your prediction for Microsoft stock?',
                'expected_direction': 'up',
                'expected_keywords': ['up', 'rise', 'bullish', 'positive'],
                'explanation': 'Microsoft shows consistent growth with stable upward movement.',
                'difficulty': 'easy',
                'base_score': 10,
                'max_score': 20,
            },
            {
                'stock_name': 'Tesla Inc.',
                'stock_symbol': 'TSLA',
                'question': 'Analyze the chart and predict Tesla\'s stock movement.',
                'expected_direction': 'down',
                'expected_keywords': ['down', 'fall', 'decline', 'bearish', 'drop'],
                'explanation': 'The chart shows a downward trend with declining volume, indicating bearish sentiment.',
                'difficulty': 'medium',
                'base_score': 12,
                'max_score': 25,
            },
            {
                'stock_name': 'Amazon.com Inc.',
                'stock_symbol': 'AMZN',
                'question': 'What do you think will happen to Amazon stock based on this chart?',
                'expected_direction': 'neutral',
                'expected_keywords': ['stable', 'flat', 'neutral', 'sideways', 'consolidate'],
                'explanation': 'Amazon is showing consolidation with price moving sideways, indicating uncertainty.',
                'difficulty': 'medium',
                'base_score': 12,
                'max_score': 25,
            },
            {
                'stock_name': 'Google (Alphabet Inc.)',
                'stock_symbol': 'GOOGL',
                'question': 'Based on the technical indicators shown, predict Google\'s stock performance.',
                'expected_direction': 'up',
                'expected_keywords': ['up', 'rise', 'bullish', 'momentum'],
                'explanation': 'Strong technical indicators suggest continued upward movement.',
                'difficulty': 'hard',
                'base_score': 15,
                'max_score': 30,
            },
            {
                'stock_name': 'Meta Platforms Inc.',
                'stock_symbol': 'META',
                'question': 'Analyze the chart pattern and make a prediction for Meta stock.',
                'expected_direction': 'down',
                'expected_keywords': ['down', 'fall', 'bearish', 'decline'],
                'explanation': 'The chart shows a bearish pattern with declining prices.',
                'difficulty': 'medium',
                'base_score': 12,
                'max_score': 25,
            },
            {
                'stock_name': 'NVIDIA Corporation',
                'stock_symbol': 'NVDA',
                'question': 'What is your prediction for NVIDIA stock based on the price action?',
                'expected_direction': 'up',
                'expected_keywords': ['up', 'rise', 'bullish', 'strong'],
                'explanation': 'NVIDIA shows strong momentum with price breaking above resistance levels.',
                'difficulty': 'hard',
                'base_score': 15,
                'max_score': 30,
            },
            {
                'stock_name': 'JPMorgan Chase & Co.',
                'stock_symbol': 'JPM',
                'question': 'Based on the chart, how do you think JPMorgan stock will move?',
                'expected_direction': 'neutral',
                'expected_keywords': ['stable', 'neutral', 'sideways', 'range'],
                'explanation': 'The stock is trading in a range, showing neutral sentiment.',
                'difficulty': 'easy',
                'base_score': 10,
                'max_score': 20,
            },
            {
                'stock_name': 'Bank of America Corp',
                'stock_symbol': 'BAC',
                'question': 'Analyze the chart and predict Bank of America\'s stock direction.',
                'expected_direction': 'up',
                'expected_keywords': ['up', 'rise', 'bullish', 'recovery'],
                'explanation': 'The chart shows a recovery pattern with upward momentum.',
                'difficulty': 'medium',
                'base_score': 12,
                'max_score': 25,
            },
            {
                'stock_name': 'Walmart Inc.',
                'stock_symbol': 'WMT',
                'question': 'What is your prediction for Walmart stock based on the technical analysis?',
                'expected_direction': 'up',
                'expected_keywords': ['up', 'rise', 'bullish', 'growth'],
                'explanation': 'Walmart shows steady growth with positive technical indicators.',
                'difficulty': 'easy',
                'base_score': 10,
                'max_score': 20,
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

