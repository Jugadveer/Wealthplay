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
    Corrects conflicts between confidence and recommendation.
    """
    stock_type = stock.stock_type
    name = stock.name
    
    # 1. Determine base sentiment from price action
    if change_pct > 1.5:
        base_sentiment = "Bullish"
    elif change_pct < -1.5:
        base_sentiment = "Bearish"
    else:
        base_sentiment = "Neutral"

    # 2. Derive confidence from trend strength and magnitude of change
    # Strong correlation: higher change = higher confidence in a trend
    abs_change = abs(float(change_pct))
    base_confidence = 0.4 + (min(abs_change, 5.0) / 10.0) # 0.4 to 0.9 range
    confidence = round(base_confidence + random.uniform(-0.05, 0.05), 2)
    confidence = max(0.1, min(0.99, confidence))

    # 3. Decision mapping based on confidence threshold
    # Strict enforcement: anything under 60% is a Hold/Wait to avoid weak signals
    if confidence < 0.60:
        recommendation = "Hold"
        final_sentiment = "Neutral"
        sentiment_word = "stable"
    else:
        if base_sentiment == "Bullish":
            recommendation = "Buy"
            final_sentiment = "Bullish"
            sentiment_word = "strong positive"
        elif base_sentiment == "Bearish":
            recommendation = "Sell"
            final_sentiment = "Bearish"
            sentiment_word = "weak"
        else:
            recommendation = "Hold"
            final_sentiment = "Neutral"
            sentiment_word = "sideways"

    # 4. Diversified Technical Narratives
    insights = {
        'tech': [
            f"Watching for break-out above resistance. RSI indicates healthy momentum.",
            f"Benefiting from sector-wide scalability. Support is holding at current levels.",
            f"Technical indicators suggest a cooling period after significant tech-sector rallies."
        ],
        # ... (rest of the categories similarly improved for variety)
        'growth': [
            f"Showing classic aggressive growth patterns. High capital expenditure reported.",
            f"Market sentiment is driven by future revenue projections. High volatility expected.",
            f"Venture inflows are increasing, supporting current price levels."
        ],
        'penny': [
            f"Liquidity is tightening. Speculative interest remains extremely high risk.",
            f"Mean reversion is likely without volume support. Watch for gap-fills.",
            f"Retail interest is at peak levels. High probability of volatility spikes."
        ],
        'stable': [
            f"Safe haven with consistent cash flows and low beta. Ideal for defensive plays.",
            f"Protected against broader market sell-offs. Institutional accumulation detected.",
            f"Dividend yield is attracting long-term interest despite slow capital growth."
        ]
    }
    
    reasoning_list = insights.get(stock_type, ["Standard market correlation. Indicators are within expected ranges."])
    tech_reasoning = random.choice(reasoning_list)
    
    # 5. Target Price calculation relative to recommendation
    if recommendation == "Buy":
        target = current_price * (1 + random.uniform(0.05, 0.12))
    elif recommendation == "Sell":
        target = current_price * (1 - random.uniform(0.05, 0.12))
    else:
        target = current_price * (1 + random.uniform(-0.02, 0.02))

    return {
        "analysis": f"{name} is showing {sentiment_word} momentum. {tech_reasoning}",
        "recommendation": recommendation,
        "sentiment": final_sentiment,
        "confidence": confidence,
        "target_price": round(target, 2)
    }
