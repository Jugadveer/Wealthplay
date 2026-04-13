import random
from decimal import Decimal
from datetime import datetime, timezone

def simulate_stock_movement(stock):
    """
    Simulate realistic market movement for a custom stock based on its type.
    This creates algorithmic behavior patterns for practice.
    """
    current_price = float(stock.current_price)
    volatility = float(stock.volatility or 0.02)
    trend_strength = float(stock.trend_strength or 0.0)
    stock_type = stock.stock_type
    
    # 1. Base Drifts & Behaviours
    drift = 0.0001 # Small global positive drift
    
    if stock_type == 'growth':
        # Growth: High variance, strong positive skew
        drift += 0.0008
        volatility *= 1.5
    elif stock_type == 'volatile' or stock_type == 'penny':
        # Speculative: High noise, chance of large jumps
        drift -= 0.0002 # Slightly lower base to offset random spikes
        volatility *= 2.5
    elif stock_type == 'stable' or stock_type == 'dividend':
        # Defensive: Low variance, mean reverting
        volatility *= 0.5
        drift += 0.0002
    elif stock_type == 'tech':
        # Tech: Fast movements, sensitive to momentum
        volatility *= 1.2
        drift += 0.0005
    
    # 2. Add "Market Sentiment" & Algorithmic Patterns
    epsilon = random.gauss(0, 1)
    
    # Special: Poisson Jumps for Volatile/Penny stocks
    jump = 0
    if stock_type in ['volatile', 'penny'] and random.random() < 0.05: # 5% chance per tick
        jump = random.uniform(-0.1, 0.1) # Large 10% jump
        
    # Special: Mean Reversion for Stable stocks
    if stock_type == 'stable':
        target_price = float(stock.base_price)
        reversion_speed = 0.05
        # Move towards base_price
        drift += reversion_speed * (target_price - current_price) / current_price

    # Trend influence (if set)
    if stock.trend == 'bullish':
        drift += trend_strength * 0.005
    elif stock.trend == 'bearish':
        drift -= trend_strength * 0.005
        
    delta_p = drift + volatility * epsilon + jump
    new_price = current_price * (1 + delta_p)
    
    # Price boundaries (Penny stock floor)
    if stock_type == 'penny':
        new_price = max(0.01, new_price)
    else:
        new_price = max(1.0, new_price)
        
    # Update change percent
    prev_price = float(stock.base_price or current_price)
    change_pct = ((new_price - prev_price) / prev_price) * 100
    
    return Decimal(str(round(new_price, 2))), Decimal(str(round(change_pct, 2)))

def generate_stock_analysis(stock, current_price, change_pct):
    """
    Algorithmically generate AI-style analysis for a stock.
    In a real app, this would call Gemini.
    """
    sentiment = "Neutral"
    if change_pct > 2: sentiment = "Bullish"
    elif change_pct < -2: sentiment = "Bearish"
    
    tech_reasoning = ""
    stock_type = stock.stock_type
    
    if stock_type == 'tech' or stock_type == 'growth':
        tech_reasoning = "High demand for AI infrastructure and cloud scalability is driving market sentiment. Watch for support levels near previous highs."
    elif stock_type == 'penny' or stock_type == 'volatile':
        tech_reasoning = "Extreme speculative interest. Liquidity is tightening. High risk of mean reversion if volume drops."
    elif stock_type == 'stable' or stock_type == 'dividend':
        tech_reasoning = "Solid fundamentals and consistent cash flow. Defensive positioning makes it a safe haven amid broader market volatility."
    else:
        tech_reasoning = "Standard market correlation. Momentum indicators are oscillating within expected ranges."
        
    return {
        "analysis": f"{stock.name} is showing {sentiment} momentum. {tech_reasoning}",
        "recommendation": "Buy" if change_pct > 1 else ("Sell" if change_pct < -1 else "Hold"),
        "confidence": round(random.uniform(0.6, 0.95), 2),
        "target_price": round(current_price * (1 + random.uniform(0.05, 0.15)), 2)
    }
