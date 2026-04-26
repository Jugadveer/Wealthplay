import os
import django
import json
import random

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wealthplay.settings')
django.setup()

from users.models import StockPredictionQuestion

def create_advanced_questions():
    """Seed advanced chart patterns for the prediction game"""
    
    advanced_patterns = [
        {
            "stock_name": "Nebula Cloud Solutions",
            "stock_symbol": "NEBU",
            "difficulty": "advanced",
            "question": "The chart shows a 'Head and Shoulders' pattern forming after a long uptrend. The right shoulder is lower than the left, and the price just broke the neckline. What is the likely next move?",
            "expected_direction": "down",
            "expected_keywords": ["head and shoulders", "reversal", "neckline", "bearish", "breakdown"],
            "explanation": "A Head and Shoulders breakdown is a classic bearish reversal signal indicating the end of an uptrend.",
            "base_score": 30,
            "max_score": 50,
            "chart_data": [
                {"date": "2024-01-01", "price": 100}, {"date": "2024-01-05", "price": 120},
                {"date": "2024-01-10", "price": 140}, {"date": "2014-01-15", "price": 110}, # Neck 1
                {"date": "2024-01-20", "price": 160}, # Head
                {"date": "2024-01-25", "price": 115}, # Neck 2
                {"date": "2024-01-30", "price": 135}, # Right Shoulder
                {"date": "2024-02-05", "price": 95}   # Breakdown
            ]
        },
        {
            "stock_name": "Titanium Heavy Industries",
            "stock_symbol": "TITN",
            "difficulty": "intermediate",
            "question": "A 'Double Bottom' has formed at the $45 support level. The price is now approaching the 'Neckline' at $52 with increasing volume. What should you expect?",
            "expected_direction": "up",
            "expected_keywords": ["double bottom", "support", "neckline", "breakout", "bullish"],
            "explanation": "A Double Bottom suggests strong support at a specific price floor, often leading to a bullish trend reversal once the neckline is cleared.",
            "base_score": 20,
            "max_score": 40,
            "chart_data": [
                {"date": "2024-01-01", "price": 60}, {"date": "2024-01-10", "price": 45}, # Bottom 1
                {"date": "2024-01-15", "price": 52}, # Neck
                {"date": "2024-01-20", "price": 46}, # Bottom 2
                {"date": "2024-01-25", "price": 54}  # Breakout
            ]
        },
        {
            "stock_name": "Quantum Bio-Tech",
            "stock_symbol": "QBIT",
            "difficulty": "advanced",
            "question": "The stock has entered a 'Rising Wedge' pattern during a brief rally in a broader bear market. Price is squeezing against the lower trendline. What is the highest probability outcome?",
            "expected_direction": "down",
            "expected_keywords": ["wedge", "bearish", "squeeze", "exhaustion", "reversal"],
            "explanation": "A Rising Wedge in a bear market is typically a bearish continuation pattern, signaling that the recent rally is losing momentum.",
            "base_score": 30,
            "max_score": 50,
            "chart_data": [
                {"date": "2024-01-01", "price": 200}, {"date": "2024-01-05", "price": 150},
                {"date": "2024-01-10", "price": 160}, {"date": "2024-01-15", "price": 155},
                {"date": "2024-01-20", "price": 170}, {"date": "2024-01-25", "price": 168},
                {"date": "2024-02-01", "price": 140}
            ]
        }
    ]

    for q in advanced_patterns:
        StockPredictionQuestion.objects.update_or_create(
            stock_symbol=q['stock_symbol'],
            difficulty=q['difficulty'],
            defaults=q
        )
    
    print(f"Successfully seeded {len(advanced_patterns)} advanced questions.")

if __name__ == "__main__":
    create_advanced_questions()
