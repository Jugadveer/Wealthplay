import os
import django
import sys
from decimal import Decimal
import random
from datetime import datetime, timedelta
import json

# Setup django
sys.path.append('d:\\Bios')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wealthplay.settings')
django.setup()

from users.models import StockPredictionQuestion, CustomStock

def generate_mock_history(base_price, trend='neutral', length=30):
    history = []
    current_price = float(base_price)
    volatility = 0.02
    
    for i in range(length):
        drift = 0
        if trend == 'up': drift = 0.005
        elif trend == 'down': drift = -0.005
        
        change = current_price * (drift + volatility * random.gauss(0, 1))
        current_price += change
        
        date = (datetime.now() - timedelta(days=length-i)).isoformat()
        
        # Add basic MAs
        history.append({
            "date": date,
            "price": round(current_price, 2),
            "volume": random.randint(1000000, 5000000),
            "ma20": round(current_price * 0.98, 2),
            "ma50": round(current_price * 0.95, 2)
        })
    return history

def seed_questions():
    # Remove old ones
    StockPredictionQuestion.objects.all().delete()
    
    questions = [
        {
            "symbol": "NSYC",
            "name": "NeuralSync (Custom Stock)",
            "question": "The stock has successfully tested its 20-day moving average three times this week. Given the upcoming expansion into neuro-gaming, where do you see the price in 30 days?",
            "trend": "up",
            "keywords": ["expansion", "gaming", "bullish", "support", "rise", "grow"],
            "explanation": "Strong support at the MA20 and fundamental gaming catalysts suggest a bullish breakout is imminent."
        },
        {
            "symbol": "QFUL",
            "name": "QuantumFuel (Custom Stock)",
            "question": "The RSI is currently at 85 after a vertical rally. Regulatory concerns about cold-fusion safety are surfacing. What is your 1-week outlook?",
            "trend": "down",
            "keywords": ["overbought", "rsi", "correction", "regulatory", "fall", "drop", "bearish"],
            "explanation": "An overextended RSI combined with regulatory headwinds typically leads to a mean-reversion correction."
        },
        {
            "symbol": "NXCR",
            "name": "NexusCore (Custom Stock)",
            "question": "The chart shows a classic 'Head and Shoulders' pattern forming on the daily timeframe. Major infrastructure reports are mixed. Predict the next move.",
            "trend": "down",
            "keywords": ["head and shoulders", "pattern", "bearish", "reversal", "fall", "breakdown"],
            "explanation": "The Head and Shoulders pattern is a classic bearish reversal indicator, suggesting price exhaustion."
        }
    ]
    
    for q in questions:
        StockPredictionQuestion.objects.create(
            stock_symbol=q['symbol'],
            stock_name=q['name'],
            question=q['question'],
            chart_data=generate_mock_history(100 if q['trend'] == 'up' else 200, q['trend']),
            expected_direction=q['trend'],
            expected_keywords=q['keywords'],
            explanation=q['explanation'],
            difficulty='medium'
        )
        print(f"Created question for {q['symbol']}")

if __name__ == "__main__":
    seed_questions()
