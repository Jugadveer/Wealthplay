"""
Portfolio API endpoints for demo trading simulator
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta, datetime, date
from decimal import Decimal
import json
import random
import os

import requests

# --- UPDATED IMPORTS ---
import yfinance as yf
import pandas as pd
from .ml_predictor import ML_PREDICTOR, TICKERS, get_stock_info, get_stock_price
# -----------------------

from .models import (
    UserProfile,
    DemoPortfolio,
    PredictedStockData,
    PortfolioFollow,
    TradeRationalePost,
    ChallengeLeaderboard,
)


USD_TO_INR_FALLBACK = Decimal('85')


def _get_groq_stock_insight(symbol, stock_info, prediction_results):
    """Generate LLM-based recommendation using Groq; return None on any failure."""
    keys = [
        (os.environ.get('GROQ_API_KEY') or '').strip(),
        (os.environ.get('GROQ_API_KEY_2') or '').strip()
    ]
    keys = [k for k in keys if k]
    if not keys:
        return None

    model = (os.environ.get('GROQ_MODEL') or 'llama-3.1-8b-instant').strip()

    prompt = (
        "You are an Elite Financial Quant Analyst. "
        "Analyze the following stock snapshot and ML signals to provide a precise recommendation. "
        "Return a strict JSON object with keys: "
        "recommendation (BUY|SELL|HOLD|WAIT), confidence (0.0 to 1.0), message (concise pedagogical insight), "
        "reasons (array of 3 distinct technical reasons), trend (BULLISH|BEARISH|NEUTRAL).\n\n"
        f"SYMBOL: {symbol}\n"
        f"ENTITY: {stock_info.get('name', symbol)}\n"
        f"PRICE: ₹{stock_info.get('current_price', 0)}\n"
        f"VOLATILITY: {prediction_results.get('vol', 0.02):.4f}\n"
        f"MARKET REGIME: {prediction_results.get('regime', 'Normal')}\n"
        f"PREDICTED DIRECTION: {prediction_results.get('direction', 'neutral')}\n"
        f"ML CONFIDENCE: {prediction_results.get('confidence', 0.5):.2f}\n"
        "Ensure the recommendation strictly aligns with the ML confidence and regime."
    )

    payload = {
        'model': model,
        'messages': [
            {
                'role': 'system',
                'content': 'Return only valid JSON. Keep output concise and educational.',
            },
            {
                'role': 'user',
                'content': prompt,
            },
        ],
        'temperature': 0.0,
        'max_tokens': 400,
    }

    content = ''

    # Try each key until one succeeds
    for api_key in keys:
        try:
            response = requests.post(
                'https://api.groq.com/openai/v1/chat/completions',
                json=payload,
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json',
                },
                timeout=20,
            )
            response.raise_for_status()
            data = response.json()

            choices = data.get('choices', [])
            if not choices:
                continue

            content = choices[0].get('message', {}).get('content', '').strip()
            if content:
                break
        except Exception as e:
            print(f"[Groq] API error with key ending in ..{api_key[-4:]}: {e}")
            continue

    if not content:
        return None

    if '```json' in content:
        content = content.split('```json', 1)[1].split('```', 1)[0].strip()
    elif '```' in content:
        content = content.split('```', 1)[1].split('```', 1)[0].strip()

    try:
        parsed = json.loads(content)
        rec = str(parsed.get('recommendation', 'WAIT')).upper()
        if rec not in {'BUY', 'SELL', 'HOLD', 'WAIT'}:
            rec = 'WAIT'

        confidence = parsed.get('confidence', 0.5)
        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 0.5
        confidence = max(0.0, min(1.0, confidence))

        reasons = parsed.get('reasons', [])
        if not isinstance(reasons, list):
            reasons = []
        reasons = [str(item) for item in reasons if str(item).strip()][:4]

        return {
            'recommendation': rec,
            'confidence': confidence,
            'message': str(parsed.get('message', 'LLM insight generated from current market context.')),
            'reasons': reasons,
            'trend': str(parsed.get('trend', 'NEUTRAL')).upper(),
            'source': 'groq',
            'model': model,
        }
    except Exception as e:
        print(f"[Groq] LLM insight parse failed for {symbol}: {e}")
        return None


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_tickers_info(request):
    """Batch fetch info for multiple tickers (used for goal strategy visualization)"""
    symbols = request.GET.get('symbols', '').split(',')
    symbols = [s.strip().upper() for s in symbols if s.strip()]
    
    if not symbols:
        return Response({'results': {}})
        
    results = {}
    for sym in symbols:
        info = get_stock_info(sym, use_cache=True, allow_live_fetch=True)
        # Add historical trends
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period='max') # Fetch all to calculate different windows
            if not hist.empty:
                current = float(hist['Close'].iloc[-1])
                
                # Helper to calculate returns
                def get_ret(days):
                    if len(hist) > days:
                        prev = float(hist['Close'].iloc[-days])
                        return round(((current - prev) / prev) * 100, 2)
                    return None

                info['returns'] = {
                    '1y': get_ret(252),
                    '3y': get_ret(252 * 3),
                    '5y': get_ret(252 * 5),
                    '10y': get_ret(252 * 10),
                    'max': round(((current - float(hist['Close'].iloc[0])) / float(hist['Close'].iloc[0])) * 100, 2)
                }
            else:
                info['returns'] = {}
        except Exception as e:
            print(f"Error calculating returns for {sym}: {e}")
            info['returns'] = {}
            
        results[sym] = info
        
    return Response({'results': results})


def get_usd_to_inr_rate():
    """Fetch USD/INR exchange rate with a safe fallback."""
    try:
        fx = yf.Ticker('INR=X')
        hist = fx.history(period='1d')
        if not hist.empty and 'Close' in hist.columns:
            rate = Decimal(str(float(hist['Close'].iloc[-1])))
            if rate > 0:
                return rate
    except Exception:
        pass
    return USD_TO_INR_FALLBACK


def convert_to_inr(amount, currency, usd_to_inr):
    """Convert an amount to INR while preserving INR values as-is."""
    value = Decimal(str(amount or 0))
    if (currency or 'INR').upper() == 'USD':
        return value * usd_to_inr
    return value


def _format_market_cap(value):
    """Convert numeric market cap to compact string (e.g., 2.4T, 450B)."""
    if not value:
        return 'N/A'
    try:
        v = float(value)
    except (TypeError, ValueError):
        return 'N/A'

    if v >= 1_000_000_000_000:
        return f"{v / 1_000_000_000_000:.2f}T"
    if v >= 1_000_000_000:
        return f"{v / 1_000_000_000:.2f}B"
    if v >= 1_000_000:
        return f"{v / 1_000_000:.2f}M"
    return f"{v:.0f}"


def _sector_esg_profile(sector):
    """Return simplified ESG and carbon profile by sector for educational scoring."""
    sector_key = (sector or 'Other').strip().lower()
    profile_map = {
        'technology': {'esg_score': 74, 'carbon_intensity': 38, 'tag': 'moderate-footprint'},
        'information technology': {'esg_score': 74, 'carbon_intensity': 38, 'tag': 'moderate-footprint'},
        'energy': {'esg_score': 42, 'carbon_intensity': 86, 'tag': 'high-footprint'},
        'oil & gas': {'esg_score': 34, 'carbon_intensity': 92, 'tag': 'high-footprint'},
        'utilities': {'esg_score': 56, 'carbon_intensity': 70, 'tag': 'improving'},
        'healthcare': {'esg_score': 78, 'carbon_intensity': 30, 'tag': 'resilient'},
        'consumer defensive': {'esg_score': 72, 'carbon_intensity': 35, 'tag': 'balanced'},
        'financial services': {'esg_score': 68, 'carbon_intensity': 28, 'tag': 'balanced'},
        'finance': {'esg_score': 68, 'carbon_intensity': 28, 'tag': 'balanced'},
        'industrials': {'esg_score': 58, 'carbon_intensity': 63, 'tag': 'transition-sensitive'},
        'materials': {'esg_score': 52, 'carbon_intensity': 74, 'tag': 'transition-sensitive'},
        'real estate': {'esg_score': 60, 'carbon_intensity': 57, 'tag': 'improving'},
        'communication services': {'esg_score': 67, 'carbon_intensity': 33, 'tag': 'balanced'},
    }
    return profile_map.get(sector_key, {'esg_score': 64, 'carbon_intensity': 46, 'tag': 'balanced'})


def _calculate_portfolio_esg(holdings):
    holdings = holdings or []
    if not holdings:
        return {
            'portfolio_esg_score': 0,
            'portfolio_carbon_intensity': 0,
            'mentor_challenge': 'Build a portfolio first, then optimize for both profit and planet.',
            'top_positive_sector': None,
            'top_negative_sector': None,
        }

    total_value = sum(float(h.get('current_value') or 0.0) for h in holdings)
    if total_value <= 0:
        total_value = 1.0

    weighted_esg = 0.0
    weighted_carbon = 0.0
    sector_scores = []
    for h in holdings:
        sector = h.get('sector') or 'Other'
        value = float(h.get('current_value') or 0.0)
        weight = value / total_value
        profile = _sector_esg_profile(sector)
        weighted_esg += weight * profile['esg_score']
        weighted_carbon += weight * profile['carbon_intensity']
        sector_scores.append((sector, profile['esg_score'], profile['carbon_intensity'], weight))

    sector_scores.sort(key=lambda x: x[1], reverse=True)
    top_positive_sector = sector_scores[0][0] if sector_scores else None
    sector_scores.sort(key=lambda x: x[2], reverse=True)
    top_negative_sector = sector_scores[0][0] if sector_scores else None

    mentor_challenge = (
        f"You made gains, but your portfolio carbon intensity is {weighted_carbon:.1f}. "
        f"Can you keep returns while shifting part of exposure away from {top_negative_sector}?"
    )

    return {
        'portfolio_esg_score': round(weighted_esg, 1),
        'portfolio_carbon_intensity': round(weighted_carbon, 1),
        'mentor_challenge': mentor_challenge,
        'top_positive_sector': top_positive_sector,
        'top_negative_sector': top_negative_sector,
    }


def _historical_event_narrative(dt):
    """Return short educational news narration for key market eras."""
    if date(2008, 9, 1) <= dt <= date(2009, 6, 30):
        return 'Global credit stress dominates headlines; liquidity concerns pressure risk assets.'
    if date(2020, 2, 15) <= dt <= date(2020, 6, 30):
        return 'Pandemic shock period: policy intervention and volatility spikes reshape market direction.'
    if date(2022, 1, 1) <= dt <= date(2022, 12, 31):
        return 'Inflation and rate-hike cycle drive valuation compression in growth-heavy sectors.'
    return 'Macro conditions are mixed; sector rotation and risk management remain key.'


# --- REMOVAL: SAMPLE_STOCKS removed, replaced by live data ---


def get_stock_info(symbol, use_cache=True, allow_live_fetch=True):
    """
    Fetch basic stock info - uses cached data for instant response.
    Falls back to live API if cache is missing or stale.
    Returns prices in appropriate currency (INR for Indian stocks, USD for US stocks).
    """
    # First check if it's a custom stock
    from .models import CustomStock
    try:
        custom_stock = CustomStock.objects.get(symbol=symbol)
        esg = _sector_esg_profile(custom_stock.sector)
        return {
            'symbol': custom_stock.symbol,
            'name': custom_stock.name,
            'current_price': float(custom_stock.current_price),
            'change_percent': float(custom_stock.change_percent),
            'category': custom_stock.category,
            'sector': custom_stock.sector,
            'market_cap': custom_stock.market_cap,
            'full_ticker': symbol,  # Custom stocks don't have full ticker
            'currency': custom_stock.currency or 'INR',
            'esg_score': esg['esg_score'],
            'carbon_intensity': esg['carbon_intensity'],
            'esg_tag': esg['tag'],
        }
    except CustomStock.DoesNotExist:
        pass  # Fall through to real stock lookup
    
    # Determine if it's an Indian stock
    from users.ml_predictor import NSE_TICKERS
    is_indian_stock = symbol.upper() in NSE_TICKERS
    
    # Try cache first for instant response
    if use_cache:
        try:
            cached = PredictedStockData.objects.get(symbol=symbol)
            # Check if cache is fresh (updated within last 10 minutes)
            cache_age = timezone.now() - cached.last_updated
            if cache_age.total_seconds() < 600:  # 10 minutes
                esg = _sector_esg_profile(cached.sector)
                return {
                    'symbol': symbol,
                    'name': cached.name,
                    'current_price': float(cached.current_price),
                    'change_percent': float(cached.change_percent),
                    'category': cached.category,
                    'sector': cached.sector,
                    'market_cap': cached.market_cap,
                    'full_ticker': ML_PREDICTOR._get_full_ticker(symbol),
                    'currency': 'INR' if is_indian_stock else 'USD',
                    'esg_score': esg['esg_score'],
                    'carbon_intensity': esg['carbon_intensity'],
                    'esg_tag': esg['tag'],
                }
        except PredictedStockData.DoesNotExist:
            pass  # Fall through to live fetch
    
    if not allow_live_fetch:
        esg = _sector_esg_profile('Other')
        return {
            'symbol': symbol,
            'name': symbol,
            'current_price': 0.0,
            'change_percent': 0.0,
            'category': 'Unknown',
            'sector': 'Unknown',
            'market_cap': 'N/A',
            'currency': 'INR' if is_indian_stock else 'USD',
            'esg_score': esg['esg_score'],
            'carbon_intensity': esg['carbon_intensity'],
            'esg_tag': esg['tag'],
        }

    # Fallback to live API if cache miss or stale
    full_ticker = ML_PREDICTOR._get_full_ticker(symbol)
    try:
        ticker = yf.Ticker(full_ticker)
        info = ticker.info
        
        name = info.get('longName') or info.get('shortName') or symbol
        sector = info.get('sector') or 'Other'
        esg = _sector_esg_profile(sector)
        market_cap_usd = info.get('marketCap')
        market_cap_display = _format_market_cap(market_cap_usd)
        
        category = 'Large Cap' 
        if market_cap_usd and market_cap_usd < 5000000000: 
            category = 'Small Cap'
        
        # Reliability enhancement: Try info first, then history fallback
        current_price = info.get('regularMarketPrice') or info.get('currentPrice') or info.get('price')
        
        # history(period="1d") is much more reliable for real-time price in yf
        if not current_price:
            hist = ticker.history(period="1d")
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
        
        # Get 1-day change percent
        history = ticker.history(period="1d", interval="1d")
        change_percent = 0
        if not history.empty and len(history) > 0 and 'Close' in history.columns:
             close = history['Close'].iloc[-1]
             open_price = history['Open'].iloc[-1]
             change_percent = ((close - open_price) / open_price) * 100 if open_price else 0
        
        return {
            'symbol': symbol,
            'name': name,
            'current_price': round(float(current_price), 2) if current_price else 0.0,
            'change_percent': round(change_percent, 2),
            'category': category,
            'sector': sector,
            'market_cap': market_cap_display,
            'full_ticker': full_ticker,
            'currency': 'INR' if is_indian_stock else 'USD',
            'esg_score': esg['esg_score'],
            'carbon_intensity': esg['carbon_intensity'],
            'esg_tag': esg['tag'],
        }
    except Exception as e:
        esg = _sector_esg_profile('Other')
        return {
            'symbol': symbol,
            'name': f"{symbol} (Data Unavailable)",
            'current_price': 0.0,
            'change_percent': 0.0,
            'category': 'Unknown',
            'sector': 'Unknown',
            'market_cap': 'N/A',
            'currency': 'INR' if is_indian_stock else 'USD',
            'esg_score': esg['esg_score'],
            'carbon_intensity': esg['carbon_intensity'],
            'esg_tag': esg['tag'],
        }


def get_stock_price(symbol, use_cache=True, allow_live_fetch=True):
    """Get current price for a stock - handles both custom and real stocks"""
    from .models import CustomStock
    try:
        custom_stock = CustomStock.objects.get(symbol=symbol)
        return float(custom_stock.current_price)
    except CustomStock.DoesNotExist:
        pass
    info = get_stock_info(symbol, use_cache=use_cache, allow_live_fetch=allow_live_fetch)
    return info.get('current_price', 0.0)


def generate_price_history(symbol, days=60, use_cache=True):
    """
    Generate price history for a stock - uses cached data for instant response.
    Falls back to live API if cache is missing.
    """
    # First check if it's a custom stock
    from .models import CustomStock
    try:
        custom_stock = CustomStock.objects.get(symbol=symbol)
        history = custom_stock.price_history or []
        return history[-days:] if len(history) > days else history
    except CustomStock.DoesNotExist:
        pass  # Fall through to real stock lookup
    
    # Try cache first for instant response

    if use_cache:
        try:
            cached = PredictedStockData.objects.get(symbol=symbol)
            cache_age = timezone.now() - cached.last_updated
            if cache_age.total_seconds() < 600:  # 10 minutes
                # Return cached history, limiting to requested days
                history = cached.price_history or []
                return history[-days:] if len(history) > days else history
        except PredictedStockData.DoesNotExist:
            pass  # Fall through to live fetch
    
    # Fallback to live API if cache miss
    full_ticker = ML_PREDICTOR._get_full_ticker(symbol)
    
    try:
        # Fetch 90 calendar days to ensure MA50 can be calculated
        df = yf.download(full_ticker, period="90d", interval="1d", progress=False, auto_adjust=True)
        if df.empty:
            return []
        
        # Handle multi-index columns from yfinance
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        # Reset index to get date as a column
        df = df.reset_index()
        
        # Handle column names - convert to lowercase strings
        new_columns = []
        for col in df.columns:
            if isinstance(col, tuple):
                # MultiIndex: take first level
                col_name = str(col[0]).lower()
            elif isinstance(col, str):
                col_name = col.lower()
            else:
                col_name = str(col).lower()
            new_columns.append(col_name)
        df.columns = new_columns
        
        # Ensure we have required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            print(f"Warning: Missing columns for {symbol}: {missing_cols}")
            return []
        
        # Rename date column if needed
        if 'date' not in df.columns:
            # Look for date-like column names
            for col in df.columns:
                if 'date' in col.lower() or col.lower() == 'index':
                    df = df.rename(columns={col: 'date'})
                    break
    except Exception as e:
        print(f"Error fetching price history for {symbol}: {e}")
        import traceback
        traceback.print_exc()
        return []

    # Calculate Moving Averages (MA20 and MA50) locally
    df['ma20'] = df['close'].rolling(window=20).mean()
    df['ma50'] = df['close'].rolling(window=50).mean()
    
    # Return the latest 'days' trading days
    df = df.tail(days)
    
    history = []
    for index, row in df.iterrows():
        history.append({
            'date': row['date'].strftime('%Y-%m-%d'),
            'price': round(row['close'], 2),
            'volume': int(row['volume']),
            'open': round(row['open'], 2),
            'high': round(row['high'], 2),
            'low': round(row['low'], 2),
            'close': round(row['close'], 2),
            'ma20': round(row['ma20'], 2) if pd.notna(row['ma20']) else None,
            'ma50': round(row['ma50'], 2) if pd.notna(row['ma50']) else None,
        })
    return history


def calculate_portfolio_data(portfolio):
    """Helper function to calculate portfolio values"""
    # Ensure holdings is a dict
    holdings = portfolio.holdings if isinstance(portfolio.holdings, dict) else {}
    if holdings is None:
        holdings = {}
    
    total_invested = Decimal('0')
    total_current_value = Decimal('0')
    holdings_list = []
    usd_to_inr = get_usd_to_inr_rate()
        
    for symbol, holding_data in holdings.items():
        try:
            if not isinstance(holding_data, dict):
                continue
            
            quantity = Decimal(str(holding_data.get('quantity', 0)))
            avg_price = Decimal(str(holding_data.get('avg_price', 0)))
            current_price_val = get_stock_price(symbol, use_cache=True, allow_live_fetch=False)
            if current_price_val <= 0:
                # If stock price not found, use avg_price as fallback
                current_price_val = float(avg_price) if avg_price > 0 else 0
            
            if quantity <= 0 or avg_price <= 0:
                continue
                
            current_price = Decimal(str(current_price_val))
            stock_info = get_stock_info(symbol, use_cache=True, allow_live_fetch=False)
            currency = (stock_info.get('currency', 'INR') or 'INR').upper()

            avg_price_inr = convert_to_inr(avg_price, currency, usd_to_inr)
            current_price_inr = convert_to_inr(current_price, currency, usd_to_inr)
            
            invested = quantity * avg_price_inr
            current_value = quantity * current_price_inr
            pnl = current_value - invested
            pnl_percent = (pnl / invested * 100) if invested > 0 else 0
            
            total_invested += invested
            total_current_value += current_value
            
            holdings_list.append({
                'symbol': symbol,
                'name': stock_info.get('name', symbol),
                'quantity': float(quantity),
                # Portfolio endpoints use INR as base currency for consistent totals.
                'avg_price': float(avg_price_inr),
                'current_price': float(current_price_inr),
                'invested': float(invested),
                'current_value': float(current_value),
                'pnl': float(pnl),
                'pnl_percent': float(pnl_percent),
                'change_percent': stock_info.get('change_percent', 0),
                'sector': stock_info.get('sector', 'Other'),
                'category': stock_info.get('category', 'Unknown'),
                'currency': 'INR',
                'quote_currency': currency,
                'fx_rate': float(usd_to_inr if currency == 'USD' else Decimal('1')),
            })
        except Exception as e:
            # Skip holdings with errors, log for debugging
            import traceback
            print(f"Error processing holding {symbol}: {e}")
            print(traceback.format_exc())
            continue
    
    # Ensure portfolio.balance is Decimal for calculation
    portfolio_balance = Decimal(str(portfolio.balance)) if not isinstance(portfolio.balance, Decimal) else portfolio.balance
    total_portfolio_value = portfolio_balance + total_current_value
    total_pnl = total_current_value - total_invested
    total_pnl_percent = (total_pnl / total_invested * 100) if total_invested > 0 else Decimal('0')
    
    return {
        'balance': float(portfolio_balance),
        'invested': float(total_invested),
        'current_value': float(total_current_value),
        'total_value': float(total_portfolio_value),
        'total_pnl': float(total_pnl),
        'total_pnl_percent': float(total_pnl_percent),
        'holdings': holdings_list,
        'holdings_count': len(holdings_list),
    }


def _snapshot_portfolio(portfolio, timestamp=None):
    """Create a chart snapshot from the current portfolio state."""
    snapshot = calculate_portfolio_data(portfolio)
    snapshot['timestamp'] = (timestamp or timezone.now()).isoformat()
    snapshot['portfolio_value'] = snapshot['total_value']
    snapshot['invested_value'] = snapshot['invested']
    snapshot['profit_value'] = snapshot['total_pnl']
    return snapshot


def _append_trade_snapshot(portfolio, timestamp=None):
    """Persist a snapshot so chart data survives reloads."""
    trade_history = portfolio.trade_history if isinstance(portfolio.trade_history, list) else []
    if not trade_history:
        trade_history.append({
            'timestamp': (timestamp or portfolio.created_at or timezone.now()).isoformat(),
            'portfolio_value': float(portfolio.balance),
            'invested_value': 0.0,
            'profit_value': 0.0,
            'balance': float(portfolio.balance),
        })

    snapshot = _snapshot_portfolio(portfolio, timestamp=timestamp)
    trade_history.append({
        'timestamp': snapshot['timestamp'],
        'portfolio_value': snapshot['portfolio_value'],
        'invested_value': snapshot['invested_value'],
        'profit_value': snapshot['profit_value'],
        'balance': snapshot['balance'],
    })
    portfolio.trade_history = trade_history[-365:]

def _clamp(value, low, high):
    return max(low, min(high, value))

def _build_conviction_analysis(symbol, quantity, current_price, average_buy_price, total_quantity_before_sale):
    """Score sell discipline vs panic behavior with simple explainable heuristics."""
    price_history = generate_price_history(symbol, days=30, use_cache=True) or []
    closes = [float(item.get('close') or item.get('price') or 0) for item in price_history]
    highs = [float(item.get('high') or item.get('price') or 0) for item in price_history]

    current = float(current_price or 0)
    avg = float(average_buy_price or 0)
    qty = float(quantity or 0)
    qty_before = float(total_quantity_before_sale or 0)
    sold_ratio = (qty / qty_before) if qty_before > 0 else 1.0

    recent_high = max(highs) if highs else current
    drop_from_recent_high = ((current - recent_high) / recent_high * 100) if recent_high > 0 else 0
    pnl_percent = ((current - avg) / avg * 100) if avg > 0 else 0

    # Approx MA20 from available closes.
    last_20 = closes[-20:] if len(closes) >= 20 else closes
    ma20 = (sum(last_20) / len(last_20)) if last_20 else current

    score = 50
    reasons = []

    if pnl_percent >= 5:
        score += 18
        reasons.append('You sold while in profit, which often indicates planned profit booking.')
    elif pnl_percent <= -8:
        score -= 18
        reasons.append('You sold at a notable loss, so this may have been an emotional exit.')

    if drop_from_recent_high <= -10 and sold_ratio > 0.5:
        score -= 15
        reasons.append('Large exit during a sharp dip suggests potential panic behavior.')

    if current < ma20 and sold_ratio <= 0.35:
        score += 10
        reasons.append('You trimmed a small portion below trend, which can be disciplined risk control.')

    if sold_ratio < 0.2:
        score += 8
        reasons.append('Partial selling keeps optionality and reflects stronger conviction.')
    elif sold_ratio > 0.8:
        score -= 8
        reasons.append('Near-full liquidation increases the chance of reactive decision-making.')

    conviction_score = int(_clamp(round(score), 0, 100))

    if conviction_score >= 70:
        behavior = 'strategy-driven'
        mentor_feedback = (
            'Strong conviction signal. Your sell appears process-led. Keep documenting exit rules so '
            'you can repeat this behavior under volatility.'
        )
    elif conviction_score >= 40:
        behavior = 'mixed-signals'
        mentor_feedback = (
            'Mixed conviction signal. Some parts look tactical, but review whether this exit matched '
            'your pre-trade plan.'
        )
    else:
        behavior = 'panic-risk'
        mentor_feedback = (
            'Low conviction signal. This sell may be fear-driven. Next time, pause and check your '
            'thesis, stop-loss rule, and position size before exiting.'
        )

    if not reasons:
        reasons.append('Trade context is limited, so this score is based on basic price-action heuristics.')

    return {
        'score': conviction_score,
        'behavior': behavior,
        'sold_ratio': round(sold_ratio, 2),
        'pnl_percent_at_sale': round(pnl_percent, 2),
        'drop_from_recent_high_percent': round(drop_from_recent_high, 2),
        'mentor_feedback': mentor_feedback,
        'reasons': reasons,
    }

def _build_proactive_mentor_nudge(portfolio_data):
    holdings = portfolio_data.get('holdings') or []
    if not holdings:
        return {
            'enabled': False,
            'message': 'Build your first position to unlock personalized portfolio nudges.',
            'risk_note': 'No diversification signal yet.',
        }

    sector_values = {}
    for holding in holdings:
        sector = holding.get('sector') or 'Other'
        sector_values[sector] = sector_values.get(sector, 0.0) + float(holding.get('current_value') or 0.0)

    total_value = sum(sector_values.values())
    if total_value <= 0:
        return {
            'enabled': False,
            'message': 'Portfolio value is too low for a reliable concentration check right now.',
            'risk_note': 'No diversification signal yet.',
        }

    sorted_sectors = sorted(sector_values.items(), key=lambda item: item[1], reverse=True)
    top_sector, top_value = sorted_sectors[0]
    top_weight = (top_value / total_value) * 100

    # Herfindahl-style diversification score where higher is better.
    hhi = sum((value / total_value) ** 2 for value in sector_values.values())
    diversification_score = int(_clamp(round((1 - hhi) * 100), 0, 100))

    if top_weight >= 55:
        alt_sector = 'Commodities' if top_sector.lower() in {'technology', 'tech', 'information technology'} else 'Healthcare'
        message = (
            f"I noticed you're heavily invested in {top_sector} stocks ({top_weight:.1f}%). "
            f"Would you like to explore diversifying into {alt_sector} to lower risk?"
        )
        risk_note = 'Concentration risk is elevated. A single-sector shock could impact your full portfolio.'
        enabled = True
    elif top_weight >= 40:
        alt_sector = 'Consumer' if top_sector.lower() in {'energy', 'commodities'} else 'Energy'
        message = (
            f"Your largest sector is {top_sector} at {top_weight:.1f}%. "
            f"A small tilt toward {alt_sector} could improve balance without major changes."
        )
        risk_note = 'Moderate concentration detected.'
        enabled = True
    else:
        message = 'Your sector spread looks balanced. Want a deeper risk check on volatility and correlation next?'
        risk_note = 'Concentration is currently healthy.'
        enabled = True

    return {
        'enabled': enabled,
        'message': message,
        'risk_note': risk_note,
        'top_sector': top_sector,
        'top_sector_weight_percent': round(top_weight, 2),
        'diversification_score': diversification_score,
    }

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_portfolio(request):
    """Get user's demo portfolio"""
    try:
        portfolio, created = DemoPortfolio.objects.get_or_create(
            user=request.user,
            defaults={
                'balance': Decimal('50000.00'),
                'holdings': {},
                'total_value': Decimal('50000.00')
            }
        )
        
        # Ensure holdings is properly initialized
        if portfolio.holdings is None:
            portfolio.holdings = {}
            portfolio.save()
        
        # Ensure balance is a Decimal
        if not isinstance(portfolio.balance, Decimal):
            portfolio.balance = Decimal(str(portfolio.balance))
            portfolio.save()
        
        # Calculate portfolio data
        portfolio_data = calculate_portfolio_data(portfolio)
        return Response(portfolio_data)
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"Error in get_portfolio: {error_msg}")
        print(traceback.format_exc())
        # Return a default portfolio structure to prevent frontend crash
        # Use status 200 so frontend doesn't treat it as an error
        return Response({
            'balance': 50000.00,
            'invested': 0.00,
            'current_value': 0.00,
            'total_value': 50000.00,
            'total_pnl': 0.00,
            'total_pnl_percent': 0.00,
            'holdings': [],
            'holdings_count': 0,
            'error': error_msg
        }, status=200)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_stocks(request):
    """Get available stocks for trading - includes both real and custom stocks"""
    try:
        from .models import CustomStock
        
        stocks = []
        
        # First, ensure custom stocks exist
        if not CustomStock.objects.exists():
            CustomStock.objects.create(symbol='WPL.AI', name='WealthPlay AI Tech', base_price=100.00, current_price=100.00, stock_type='tech', sector='AI', category='Large Cap', volatility=0.04, trend='bullish')
            CustomStock.objects.create(symbol='GBL.ENG', name='Global Energy Corp', base_price=50.00, current_price=50.00, stock_type='energy', sector='Energy', category='Mid Cap', volatility=0.02, trend='neutral')
            CustomStock.objects.create(symbol='SAFE.X', name='Safe Haven bonds', base_price=10.00, current_price=10.00, stock_type='stable', sector='Finance', category='Blue Chip', volatility=0.005, trend='bullish')

        # Algorithmic daily update for custom stocks
        today = timezone.now().date()
        custom_stocks = CustomStock.objects.all()
        from .simulator_engine import simulate_stock_movement
        for custom in custom_stocks:
            # Check if it needs a daily update
            history = custom.price_history if isinstance(custom.price_history, list) else []
            
            # SEED HISTORY IF EMPTY - ensures candlestick chart works
            if not history:
                base_p = float(custom.base_price)
                for i in range(15, 0, -1):
                    p_date = today - timedelta(days=i)
                    # Create more variance between open/close for visible candles
                    noise_o = (random.random() - 0.5) * 2 * custom.volatility * base_p
                    noise_c = (random.random() - 0.5) * 2 * custom.volatility * base_p
                    open_p = base_p + noise_o
                    close_p = base_p + noise_c
                    # Ensure high/low are actually the high/low
                    high_p = max(open_p, close_p) + (random.random() * 0.01 * base_p)
                    low_p = min(open_p, close_p) - (random.random() * 0.01 * base_p)
                    
                    history.append({
                        "date": p_date.isoformat(),
                        "price": round(close_p, 2),
                        "close": round(close_p, 2),
                        "open": round(open_p, 2),
                        "high": round(high_p, 2),
                        "low": round(low_p, 2),
                        "volume": random.randint(1000, 5000)
                    })
                custom.price_history = history
                custom.save()

            if custom.last_updated.date() < today:
                prev_price = float(custom.current_price)
                new_price, change_pct = simulate_stock_movement(custom)
                custom.current_price = new_price
                custom.change_percent = change_pct
                
                # Update history
                history.append({
                    "date": today.isoformat(),
                    "price": float(custom.current_price),
                    "close": float(custom.current_price),
                    "open": prev_price,
                    "high": max(prev_price, float(custom.current_price)),
                    "low": min(prev_price, float(custom.current_price)),
                    "volume": random.randint(1000, 5000)
                })
                # Keep last 30 days
                custom.price_history = history[-30:]
                custom.save()
        
        # Return custom stocks from persisted values.
        # Prices are updated by daily algorithmic refresh, not per-request, to avoid refresh jitter.
        custom_stocks = CustomStock.objects.filter(current_price__gt=0).order_by('symbol')
        for custom in custom_stocks:
            stocks.append({
                'symbol': custom.symbol,
                'name': custom.name,
                'current_price': float(custom.current_price),
                'change_percent': float(custom.change_percent),
                'category': custom.category,
                'sector': custom.sector,
                'market_cap': custom.market_cap,
                'currency': custom.currency or 'INR',
                'is_custom': True,  # Flag to identify custom stocks
            })
        
        # Then, add cached real stocks
        cached_stocks = PredictedStockData.objects.filter(
            current_price__gt=0
        ).order_by('symbol')
        
        for cached in cached_stocks:
            cache_age = timezone.now() - cached.last_updated
            if cache_age.total_seconds() < 600:  # 10 minutes
                stocks.append({
                    'symbol': cached.symbol,
                    'name': cached.name,
                    'current_price': float(cached.current_price),
                    'change_percent': float(cached.change_percent),
                    'category': cached.category,
                    'sector': cached.sector,
                    'market_cap': cached.market_cap,
                    'currency': cached.currency or 'USD',
                    'is_custom': False,
                })
        
        # Always include real stocks from TICKERS list (even if not in cache)
        # This ensures users can see and trade real stocks like AAPL, GOOGL, etc.
        for symbol in TICKERS:
            # Skip if already added (either as custom or cached)
            if any(s['symbol'] == symbol for s in stocks):
                continue
            try:
                info = get_stock_info(symbol, use_cache=True, allow_live_fetch=False)
                if info.get('current_price', 0.0) > 0.0:
                    info['is_custom'] = False
                    stocks.append(info)
            except Exception as e:
                # Skip stocks that fail to fetch
                print(f"Warning: Could not fetch {symbol}: {e}")
                continue
        
        return Response({'stocks': stocks})
    except Exception as e:
        import traceback
        print(f"Error in get_stocks: {e}")
        print(traceback.format_exc())
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_stock_detail(request, symbol):
    """Get detailed information about a stock - uses cached data for instant response"""
    try:
        from .models import CustomStock
        
        # First check if it's a custom stock
        try:
            custom_stock = CustomStock.objects.get(symbol=symbol)
            custom_esg = _sector_esg_profile(custom_stock.sector)
            price_history = custom_stock.price_history or []
            current_price = float(custom_stock.current_price)
            
            # Calculate summary statistics
            if price_history:
                prices = [h.get('price', h.get('close', 0)) for h in price_history]
                volumes = [h.get('volume', 0) for h in price_history]
                high_price = max(prices) if prices else current_price
                low_price = min(prices) if prices else current_price
                avg_price = sum(prices) / len(prices) if prices else current_price
                avg_volume = sum(volumes) / len(volumes) if volumes else 0
                
                latest_entry = price_history[-1] if price_history else {}
                ma20 = latest_entry.get('ma20')
                ma50 = latest_entry.get('ma50')
            else:
                high_price = low_price = avg_price = current_price
                avg_volume = 0
                ma20 = ma50 = None
            
            # Check if user owns this stock
            portfolio, _ = DemoPortfolio.objects.get_or_create(
                user=request.user,
                defaults={'balance': 50000.00, 'holdings': {}, 'total_value': 50000.00}
            )
            holdings = portfolio.holdings or {}
            holding = holdings.get(symbol, {})
            
            return Response({
                'symbol': custom_stock.symbol,
                'name': custom_stock.name,
                'current_price': current_price,
                'change_percent': float(custom_stock.change_percent),
                'category': custom_stock.category,
                'sector': custom_stock.sector,
                'market_cap': custom_stock.market_cap,
                'currency': custom_stock.currency or 'INR',
                'esg_score': custom_esg['esg_score'],
                'carbon_intensity': custom_esg['carbon_intensity'],
                'esg_tag': custom_esg['tag'],
                'price_history': price_history,
                'summary': {
                    'high': round(high_price, 2),
                    'low': round(low_price, 2),
                    'average': round(avg_price, 2),
                    'avg_volume': round(avg_volume, 0),
                    'ma20': round(ma20, 2) if ma20 else None,
                    'ma50': round(ma50, 2) if ma50 else None,
                },
                'holding': {
                    'quantity': holding.get('quantity', 0),
                        'avg_price': float(convert_to_inr(holding.get('avg_price', 0), custom_stock.currency or 'INR', get_usd_to_inr_rate())),
                        'invested': float(convert_to_inr(holding.get('quantity', 0) * holding.get('avg_price', 0), custom_stock.currency or 'INR', get_usd_to_inr_rate())),
                } if holding else None,
                'is_custom': True,
            })
        except CustomStock.DoesNotExist:
            pass  # Fall through to real stock lookup
        
        # Try to get from cache first for instant response
        try:
            cached = PredictedStockData.objects.get(symbol=symbol)
            cache_age = timezone.now() - cached.last_updated
            
            if cache_age.total_seconds() < 600:  # 10 minutes - use cache
                cached_esg = _sector_esg_profile(cached.sector)
                price_history = cached.price_history or []
                current_price = float(cached.current_price)
                
                # Calculate summary statistics from cached history
                if price_history:
                    prices = [h.get('price', h.get('close', 0)) for h in price_history]
                    volumes = [h.get('volume', 0) for h in price_history]
                    high_price = max(prices) if prices else current_price
                    low_price = min(prices) if prices else current_price
                    avg_price = sum(prices) / len(prices) if prices else current_price
                    avg_volume = sum(volumes) / len(volumes) if volumes else 0
                    
                    latest_entry = price_history[-1] if price_history else {}
                    ma20 = latest_entry.get('ma20')
                    ma50 = latest_entry.get('ma50')
                else:
                    high_price = low_price = avg_price = current_price
                    avg_volume = 0
                    ma20 = ma50 = None
                
                # Check if user owns this stock
                portfolio, _ = DemoPortfolio.objects.get_or_create(
                    user=request.user,
                    defaults={'balance': 50000.00, 'holdings': {}, 'total_value': 50000.00}
                )
                holdings = portfolio.holdings or {}
                holding = holdings.get(symbol, {})
                
                return Response({
                    'symbol': cached.symbol,
                    'name': cached.name,
                    'current_price': current_price,
                    'change_percent': float(cached.change_percent),
                    'category': cached.category,
                    'sector': cached.sector,
                    'market_cap': cached.market_cap,
                    'currency': cached.currency or 'USD',
                    'esg_score': cached_esg['esg_score'],
                    'carbon_intensity': cached_esg['carbon_intensity'],
                    'esg_tag': cached_esg['tag'],
                    'price_history': price_history,
                    'summary': {
                        'high': round(high_price, 2),
                        'low': round(low_price, 2),
                        'average': round(avg_price, 2),
                        'avg_volume': round(avg_volume, 0),
                        'ma20': round(ma20, 2) if ma20 else None,
                        'ma50': round(ma50, 2) if ma50 else None,
                    },
                    'holding': {
                        'quantity': holding.get('quantity', 0),
                        'avg_price': float(convert_to_inr(holding.get('avg_price', 0), cached.currency or 'USD', get_usd_to_inr_rate())),
                        'invested': float(convert_to_inr(holding.get('quantity', 0) * holding.get('avg_price', 0), cached.currency or 'USD', get_usd_to_inr_rate())),
                    } if holding else None,
                    'is_custom': False,
                })
        except PredictedStockData.DoesNotExist:
            pass  # Fall through to live fetch
        
        # Fallback to live data if cache miss
        stock_info = get_stock_info(symbol, use_cache=True, allow_live_fetch=True)
        if stock_info.get('current_price', 0.0) <= 0.0:
            return Response({'error': 'Stock not found'}, status=404)
        
        current_price = get_stock_price(symbol)
        price_history = generate_price_history(symbol, 60, use_cache=False)  # Generate 60 days for better MA calculations
        
        # Calculate summary statistics
        if price_history:
            prices = [h['price'] for h in price_history]
            volumes = [h['volume'] for h in price_history]
            high_price = max(prices) if prices else current_price
            low_price = min(prices) if prices else current_price
            avg_price = sum(prices) / len(prices) if prices else current_price
            avg_volume = sum(volumes) / len(volumes) if volumes else 0
            
            # Get latest MA values
            latest_entry = price_history[-1] if price_history else {}
            ma20 = latest_entry.get('ma20')
            ma50 = latest_entry.get('ma50')
        else:
            high_price = low_price = avg_price = current_price
            avg_volume = 0
            ma20 = ma50 = None
        
        # Check if user owns this stock
        portfolio, _ = DemoPortfolio.objects.get_or_create(
            user=request.user,
            defaults={'balance': 50000.00, 'holdings': {}, 'total_value': 50000.00}
        )
        holdings = portfolio.holdings or {}
        holding = holdings.get(symbol, {})
        
        return Response({
            **stock_info,
            'current_price': current_price,
            'price_history': price_history,
            'summary': {
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'average': round(avg_price, 2),
                'avg_volume': round(avg_volume, 0),
                'ma20': round(ma20, 2) if ma20 else None,
                'ma50': round(ma50, 2) if ma50 else None,
            },
            'holding': {
                'quantity': holding.get('quantity', 0),
                'avg_price': float(convert_to_inr(holding.get('avg_price', 0), stock_info.get('currency', 'INR'), get_usd_to_inr_rate())),
                'invested': float(convert_to_inr(holding.get('quantity', 0) * holding.get('avg_price', 0), stock_info.get('currency', 'INR'), get_usd_to_inr_rate())),
            } if holding else None,
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def buy_stock(request):
    """Buy stock and check for achievements"""
    from .achievement_views import check_and_unlock_achievements
    """Buy stock in demo portfolio"""
    try:
        symbol = request.data.get('symbol', '').strip().upper()
        quantity = int(request.data.get('quantity', 0))
        
        print(f"Trade Request: BUY {quantity} shares of {symbol} for user {request.user.username}")
        
        if not symbol or quantity <= 0:
            return Response({'error': 'Invalid symbol or quantity'}, status=400)
        
        stock_info = get_stock_info(symbol, use_cache=True, allow_live_fetch=False)
        current_price = get_stock_price(symbol, use_cache=True, allow_live_fetch=False)
        if current_price <= 0:
            print(f"Error: Price for {symbol} returned 0.0 or failed fetch.")
            return Response({'error': f'Stock {symbol} is temporarily unavailable for trading. Please retry in a moment.'}, status=503)

        currency = (stock_info.get('currency', 'INR') or 'INR').upper()
        usd_to_inr = get_usd_to_inr_rate()
        total_cost = convert_to_inr(Decimal(str(current_price)) * Decimal(str(quantity)), currency, usd_to_inr)
        
        portfolio, _ = DemoPortfolio.objects.get_or_create(
            user=request.user,
            defaults={'balance': Decimal('50000.00'), 'holdings': {}, 'total_value': Decimal('50000.00')}
        )
        
        # Ensure balance is Decimal type
        if not isinstance(portfolio.balance, Decimal):
            portfolio.balance = Decimal(str(portfolio.balance))
        
        if portfolio.balance < total_cost:
            return Response({'error': 'Insufficient balance'}, status=400)
        
        # Update holdings
        holdings = portfolio.holdings or {}
        if symbol in holdings:
            # Calculate new average price
            old_quantity = Decimal(str(holdings[symbol]['quantity']))
            old_avg_price = Decimal(str(holdings[symbol]['avg_price']))
            new_investment = total_cost
            
            new_quantity = old_quantity + Decimal(str(quantity))
            new_avg_price = ((old_quantity * old_avg_price) + new_investment) / new_quantity
            
            holdings[symbol] = {
                'quantity': float(new_quantity),
                'avg_price': float(new_avg_price),
            }
        else:
            holdings[symbol] = {
                'quantity': quantity,
                'avg_price': float(current_price),
            }
        
        portfolio.holdings = holdings
        # Ensure both sides are Decimal for subtraction
        if not isinstance(portfolio.balance, Decimal):
            portfolio.balance = Decimal(str(portfolio.balance))
        portfolio.balance = portfolio.balance - total_cost
        portfolio.save()
        _append_trade_snapshot(portfolio)
        portfolio.save(update_fields=['trade_history', 'balance', 'holdings', 'updated_at'])

        # Check for achievements after successful trade (including first_trade + XP rewards).
        newly_unlocked = check_and_unlock_achievements(request.user)
        
        # Calculate and return updated portfolio data
        portfolio_data = calculate_portfolio_data(portfolio)
        portfolio_data['success'] = True
        portfolio_data['message'] = f'Successfully bought {quantity} shares of {symbol}'
        portfolio_data['newly_unlocked_achievements'] = [
            {
                'id': ach.id,
                'name': ach.name,
                'xp_reward': ach.xp_reward,
            }
            for ach in newly_unlocked
        ]
        
        return Response(portfolio_data)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sell_stock(request):
    """Sell stock from demo portfolio"""
    from .achievement_views import check_and_unlock_achievements
    try:
        symbol = request.data.get('symbol')
        quantity = int(request.data.get('quantity', 0))
        
        if not symbol or quantity <= 0:
            return Response({'error': 'Invalid symbol or quantity'}, status=400)
        
        stock_info = get_stock_info(symbol, use_cache=True, allow_live_fetch=False)
        current_price = get_stock_price(symbol, use_cache=True, allow_live_fetch=False)
        if current_price <= 0:
            return Response({'error': 'Stock is temporarily unavailable for trading. Please retry in a moment.'}, status=503)
        
        portfolio, _ = DemoPortfolio.objects.get_or_create(
            user=request.user,
            defaults={'balance': Decimal('50000.00'), 'holdings': {}, 'total_value': Decimal('50000.00')}
        )
        
        # Ensure balance is Decimal type
        if not isinstance(portfolio.balance, Decimal):
            portfolio.balance = Decimal(str(portfolio.balance))
        
        holdings = portfolio.holdings or {}
        if symbol not in holdings or holdings[symbol]['quantity'] < quantity:
            return Response({'error': 'Insufficient shares'}, status=400)
        
        existing_holding = holdings[symbol]
        quantity_before_sale = float(existing_holding.get('quantity', 0))
        avg_price_before_sale = float(existing_holding.get('avg_price', 0))

        # Update holdings
        holdings[symbol]['quantity'] -= quantity
        if holdings[symbol]['quantity'] <= 0:
            del holdings[symbol]
        
        currency = (stock_info.get('currency', 'INR') or 'INR').upper()
        usd_to_inr = get_usd_to_inr_rate()
        sale_amount = convert_to_inr(Decimal(str(current_price)) * Decimal(str(quantity)), currency, usd_to_inr)
        portfolio.holdings = holdings
        # Ensure both sides are Decimal for addition
        if not isinstance(portfolio.balance, Decimal):
            portfolio.balance = Decimal(str(portfolio.balance))
        portfolio.balance = Decimal(str(portfolio.balance)) + sale_amount
        portfolio.save()
        _append_trade_snapshot(portfolio)
        portfolio.save(update_fields=['trade_history', 'balance', 'holdings', 'updated_at'])
        
        # Check for achievements after successful trade
        newly_unlocked = check_and_unlock_achievements(request.user)
        
        # Calculate and return updated portfolio data
        portfolio_data = calculate_portfolio_data(portfolio)
        portfolio_data['success'] = True
        portfolio_data['message'] = f'Successfully sold {quantity} shares of {symbol}'
        portfolio_data['conviction_analysis'] = _build_conviction_analysis(
            symbol=symbol,
            quantity=quantity,
            current_price=current_price,
            average_buy_price=avg_price_before_sale,
            total_quantity_before_sale=quantity_before_sale,
        )
        portfolio_data['newly_unlocked_achievements'] = [
            {
                'id': ach.id,
                'name': ach.name,
                'xp_reward': ach.xp_reward,
            }
            for ach in newly_unlocked
        ]
        
        return Response(portfolio_data)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_portfolio_history(request):
    """Get portfolio value history for charts"""
    try:
        days = int(request.query_params.get('days', 30))
        days = max(7, min(days, 180))

        portfolio, _ = DemoPortfolio.objects.get_or_create(
            user=request.user,
            defaults={'balance': 50000.00, 'holdings': {}, 'total_value': 50000.00}
        )

        trade_history = portfolio.trade_history if isinstance(portfolio.trade_history, list) else []
        history = []

        def _normalize_entry(entry):
            timestamp = entry.get('timestamp') or entry.get('date')
            if not timestamp:
                return None
            return {
                'timestamp': timestamp,
                'portfolio_value': float(entry.get('portfolio_value', entry.get('value', 0))),
                'invested_value': float(entry.get('invested_value', 0)),
                'profit_value': float(entry.get('profit_value', entry.get('portfolio_value', 0) - entry.get('invested_value', 0))),
            }

        for entry in trade_history:
            normalized = _normalize_entry(entry)
            if normalized:
                history.append(normalized)

        history.sort(key=lambda item: item['timestamp'])

        if history:
            return Response({'history': history[-days:]})

        # Bootstrap chart for older portfolios with no stored history yet.
        current_snapshot = _snapshot_portfolio(portfolio)
        opening_snapshot = {
            'timestamp': portfolio.created_at.isoformat(),
            'portfolio_value': 50000.0,
            'invested_value': 0.0,
            'profit_value': 0.0,
        }

        if current_snapshot['portfolio_value'] == 50000.0 and current_snapshot['invested_value'] == 0.0:
            return Response({'history': [opening_snapshot]})

        return Response({'history': [opening_snapshot, {
            'timestamp': current_snapshot['timestamp'],
            'portfolio_value': current_snapshot['portfolio_value'],
            'invested_value': current_snapshot['invested_value'],
            'profit_value': current_snapshot['profit_value'],
        }]})
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_ai_recommendation(request):
    """Get AI recommendation for stocks - handles both custom and real stocks"""
    try:
        symbol = request.data.get('symbol')
        if not symbol:
            return Response({'error': 'Symbol required'}, status=400)

        # First check if it's a custom stock
        from .models import CustomStock
        from .simulator_engine import generate_stock_analysis
        try:
            custom_stock = CustomStock.objects.get(symbol=symbol)
            analysis_data = generate_stock_analysis(custom_stock, float(custom_stock.current_price), float(custom_stock.change_percent))
            
            return Response({
                'symbol': symbol,
                'recommendation': analysis_data['recommendation'],
                'confidence': analysis_data['confidence'],
                'message': analysis_data['analysis'],
                'target_price': analysis_data['target_price'],
                'regime': 'Virtual Simulation',
                'metadata': {
                    'source': 'custom-sim',
                },
                'is_custom': True
            })
        except CustomStock.DoesNotExist:
            pass # Continue to real stocks

        # Try to get from cache first for instant response
        try:
            cached = PredictedStockData.objects.get(symbol=symbol)
            cache_age = timezone.now() - cached.last_updated
            
            if cache_age.total_seconds() < 600:  # 10 minutes - use cache
                recommendation = cached.ml_direction
                confidence = cached.ml_confidence
                regime = cached.ml_regime
                vol = cached.ml_volatility

                cached_stock_info = {
                    'name': cached.name or symbol,
                    'current_price': float(cached.current_price or 0.0),
                    'change_percent': float(cached.change_percent or 0.0),
                    'sector': cached.sector or 'Unknown',
                }
                cached_prediction_results = {
                    'direction': recommendation,
                    'confidence': float(confidence or 0.5),
                    'regime': regime or 'Calm',
                    'vol': float(vol or 0.02),
                }

                llm_insight = _get_groq_stock_insight(symbol, cached_stock_info, cached_prediction_results)
                if llm_insight:
                    return Response({
                        'symbol': symbol,
                        'recommendation': llm_insight['recommendation'],
                        'confidence': round(llm_insight['confidence'], 2),
                        'message': llm_insight['message'],
                        'reasons': llm_insight['reasons'],
                        'metadata': {
                            'regime': cached_prediction_results.get('regime', 'Calm'),
                            'volatility': round(float(cached_prediction_results.get('vol', 0.02)), 4),
                            'source': llm_insight.get('source', 'groq'),
                            'llm_model': llm_insight.get('model', ''),
                            'based_on': 'ml-cache',
                        },
                        'is_custom': False,
                    })
                
                # Convert prediction to recommendation message
                if recommendation == 'bullish':
                    message = f"ML Analysis: The model suggests an **Up** move with {round(confidence * 100)}% confidence."
                    action_text = "BUY"
                elif recommendation == 'bearish':
                    message = f"ML Analysis: The model suggests a **Down** move with {round(confidence * 100)}% confidence."
                    action_text = "SELL"
                else:
                    message = f"ML Analysis: The model is **Neutral** with {round(confidence * 100)}% confidence."
                    action_text = "HOLD"
                
                return Response({
                    'symbol': symbol,
                    'recommendation': action_text,
                    'confidence': confidence,
                    'message': message,
                    'regime': regime,
                    'metadata': {
                        'source': 'ml-cache',
                        'regime': regime,
                        'volatility': round(float(vol or 0.0), 4),
                    },
                    'is_custom': False
                })
        except PredictedStockData.DoesNotExist:
            pass  # Fall through to live prediction
        
        # Fallback to live prediction if cache miss
        stock_info = get_stock_info(symbol, use_cache=True, allow_live_fetch=True)
        if stock_info.get('current_price', 0.0) <= 0.0:
            llm_no_price = _get_groq_stock_insight(
                symbol,
                stock_info,
                {
                    'direction': 'neutral',
                    'confidence': 0.5,
                    'regime': 'Unknown',
                    'vol': 0.02,
                },
            )
            if llm_no_price:
                return Response({
                    'symbol': symbol,
                    'recommendation': llm_no_price['recommendation'],
                    'confidence': round(llm_no_price['confidence'], 2),
                    'message': llm_no_price['message'],
                    'reasons': llm_no_price['reasons'],
                    'metadata': {
                        'source': llm_no_price.get('source', 'groq'),
                        'llm_model': llm_no_price.get('model', ''),
                        'regime': 'Unknown',
                        'volatility': 0.02,
                        'based_on': 'no-live-price',
                    },
                    'is_custom': False,
                })

            return Response({
                'symbol': symbol,
                'recommendation': 'WAIT',
                'confidence': 0.5,
                'message': 'Stock data is temporarily unavailable for AI analysis. Please try again shortly.',
                'reasons': [
                    'Live data fetch returned no price for this symbol.',
                    'Using a safe fallback signal until data is refreshed.',
                ],
                'metadata': {
                    'source': 'fallback-no-price',
                    'regime': 'Unknown',
                    'volatility': 0.0,
                },
                'is_custom': False,
            }, status=200)
        
        # Run the actual ML prediction
        prediction_results = ML_PREDICTOR.predict(symbol)

        # Try LLM enrichment first (if GROQ_API_KEY is configured).
        llm_insight = _get_groq_stock_insight(symbol, stock_info, prediction_results)
        if llm_insight:
            return Response({
                'symbol': symbol,
                'recommendation': llm_insight['recommendation'],
                'confidence': round(llm_insight['confidence'], 2),
                'message': llm_insight['message'],
                'reasons': llm_insight['reasons'],
                'metadata': {
                    'regime': prediction_results.get('regime', 'Calm'),
                    'volatility': round(float(prediction_results.get('vol', 0.02)), 4),
                    'source': llm_insight.get('source', 'groq'),
                    'llm_model': llm_insight.get('model', ''),
                },
                'is_custom': False,
            })
        
        recommendation = prediction_results['direction']
        confidence = prediction_results['confidence']
        regime = prediction_results['regime']
        vol = prediction_results['vol']
        
        # Convert prediction to recommendation message
        # Threshold: Only recommend BUY/SELL if confidence >= 50%
        if confidence < 0.5:
            message = f"ML Analysis: The model is **Neutral** with {round(confidence * 100)}% confidence. Signal strength is too low for a conclusive action."
            action_text = "WAIT"
            recommendation = "neutral"
        elif recommendation == 'bullish':
            message = f"ML Analysis: The model suggests an **Up** move with {round(confidence * 100)}% confidence."
            action_text = "BUY"
        elif recommendation == 'bearish':
            message = f"ML Analysis: The model suggests a **Down** move with {round(confidence * 100)}% confidence."
            action_text = "SELL"
        else:
            message = f"ML Analysis: The model is **Neutral** with {round(confidence * 100)}% confidence."
            action_text = "HOLD"
        
        reasons = [
            f'Market Regime: Currently **{regime}** (Volatility: {round(vol * 100, 2)}%)',
            f'Confidence Level: {round(confidence * 100)}%',
            f'Predicted Action: {action_text}.'
        ]
        
        return Response({
            'symbol': symbol,
            'recommendation': action_text,
            'confidence': round(confidence, 2),
            'message': message,
            'reasons': reasons,
            'metadata': {
                'source': 'ml-live',
                'regime': regime,
                'volatility': round(vol, 4)
            },
            'is_custom': False,
        })
    except Exception as e:
        import traceback
        print(f"Error in get_ai_recommendation: {e}")
        print(traceback.format_exc())
        return Response({
            'symbol': request.data.get('symbol') or 'UNKNOWN',
            'recommendation': 'WAIT',
            'confidence': 0.5,
            'message': 'Insight generation hit a temporary issue. Returning a safe fallback recommendation.',
            'reasons': [
                'Backend encountered a transient exception while generating the insight.',
                'Please retry; live AI path should recover automatically.',
            ],
            'metadata': {
                'source': 'fallback-exception',
                'regime': 'Unknown',
                'volatility': 0.0,
            },
            'is_custom': False,
        }, status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_proactive_mentor_nudge(request):
    """Return proactive portfolio coaching prompts based on concentration and diversification."""
    try:
        portfolio, _ = DemoPortfolio.objects.get_or_create(
            user=request.user,
            defaults={'balance': Decimal('50000.00'), 'holdings': {}, 'total_value': Decimal('50000.00')}
        )
        portfolio_data = calculate_portfolio_data(portfolio)
        nudge = _build_proactive_mentor_nudge(portfolio_data)
        return Response({
            'nudge': nudge,
            'holdings_count': portfolio_data.get('holdings_count', 0),
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_portfolio_esg(request):
    """Return weighted ESG and carbon footprint signals for the user's portfolio."""
    try:
        portfolio, _ = DemoPortfolio.objects.get_or_create(
            user=request.user,
            defaults={'balance': Decimal('50000.00'), 'holdings': {}, 'total_value': Decimal('50000.00')}
        )
        portfolio_data = calculate_portfolio_data(portfolio)
        holdings = portfolio_data.get('holdings', [])

        esg_summary = _calculate_portfolio_esg(holdings)
        total_value = sum(float(h.get('current_value') or 0.0) for h in holdings) or 1.0
        holding_breakdown = []
        for h in holdings:
            profile = _sector_esg_profile(h.get('sector'))
            weight = (float(h.get('current_value') or 0.0) / total_value) * 100
            holding_breakdown.append({
                'symbol': h.get('symbol'),
                'sector': h.get('sector') or 'Other',
                'weight_percent': round(weight, 2),
                'esg_score': profile['esg_score'],
                'carbon_intensity': profile['carbon_intensity'],
                'tag': profile['tag'],
            })

        return Response({
            'summary': esg_summary,
            'holdings': holding_breakdown,
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_hindsight_replay(request):
    """Replay current holdings over historical dates with educational macro narration."""
    try:
        preset = (request.data.get('preset') or '').strip().lower()
        start_date_str = request.data.get('start_date')
        end_date_str = request.data.get('end_date')

        if preset == '2008-crash':
            start_date = date(2008, 9, 1)
            end_date = date(2009, 6, 30)
        elif preset == '2020-pandemic':
            start_date = date(2020, 2, 1)
            end_date = date(2020, 9, 1)
        else:
            if not start_date_str or not end_date_str:
                return Response({'error': 'start_date and end_date are required when preset is not provided'}, status=400)
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        if start_date >= end_date:
            return Response({'error': 'start_date must be before end_date'}, status=400)

        portfolio, _ = DemoPortfolio.objects.get_or_create(
            user=request.user,
            defaults={'balance': Decimal('50000.00'), 'holdings': {}, 'total_value': Decimal('50000.00')}
        )
        holdings = portfolio.holdings or {}
        if not holdings:
            return Response({'error': 'No holdings available for replay'}, status=400)

        usd_to_inr = get_usd_to_inr_rate()
        timeline_map = {}
        symbol_summaries = []

        for symbol, holding in holdings.items():
            quantity = float(holding.get('quantity', 0) or 0)
            if quantity <= 0:
                continue

            stock_info = get_stock_info(symbol, use_cache=True)
            full_ticker = stock_info.get('full_ticker') or ML_PREDICTOR._get_full_ticker(symbol)
            currency = (stock_info.get('currency') or 'INR').upper()

            df = yf.download(
                full_ticker,
                start=start_date.isoformat(),
                end=(end_date + timedelta(days=1)).isoformat(),
                interval='1d',
                progress=False,
                auto_adjust=True,
            )
            if df.empty:
                continue

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            df = df.reset_index()
            if 'Date' not in df.columns or 'Close' not in df.columns:
                continue

            start_close = float(df['Close'].iloc[0])
            end_close = float(df['Close'].iloc[-1])
            perf_pct = ((end_close - start_close) / start_close * 100) if start_close else 0.0
            symbol_summaries.append({
                'symbol': symbol,
                'start_close': round(start_close, 2),
                'end_close': round(end_close, 2),
                'period_return_percent': round(perf_pct, 2),
            })

            for _, row in df.iterrows():
                dt = row['Date'].date()
                close_px = float(row['Close'])
                close_inr = float(convert_to_inr(close_px, currency, usd_to_inr))
                date_key = dt.isoformat()
                if date_key not in timeline_map:
                    timeline_map[date_key] = {
                        'date': date_key,
                        'portfolio_value': float(portfolio.balance),
                    }
                timeline_map[date_key]['portfolio_value'] += quantity * close_inr

        if not timeline_map:
            return Response({'error': 'Unable to fetch historical OHLC data for current holdings'}, status=400)

        timeline = [timeline_map[k] for k in sorted(timeline_map.keys())]
        values = [point['portfolio_value'] for point in timeline]
        first_value = values[0]
        final_value = values[-1]
        max_value = max(values)
        min_value = min(values)
        replay_return = ((final_value - first_value) / first_value * 100) if first_value else 0.0
        drawdown = ((min_value - max_value) / max_value * 100) if max_value else 0.0

        events = []
        for point in timeline[::max(1, len(timeline) // 8)]:
            dt = datetime.strptime(point['date'], '%Y-%m-%d').date()
            events.append({
                'date': point['date'],
                'headline': _historical_event_narrative(dt),
            })

        return Response({
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'timeline': timeline,
            'events': events,
            'portfolio_summary': {
                'start_value': round(first_value, 2),
                'end_value': round(final_value, 2),
                'return_percent': round(replay_return, 2),
                'max_drawdown_percent': round(drawdown, 2),
            },
            'symbols': symbol_summaries,
        })
    except ValueError:
        return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_copy_trading_hub(request):
    """Get top traders, follow state, and rationale feed for copy-trading leagues."""
    try:
        followed_ids = set(
            PortfolioFollow.objects.filter(follower=request.user).values_list('followed_user_id', flat=True)
        )

        top_entries = ChallengeLeaderboard.objects.select_related('user').order_by('-total_score', '-current_streak')[:12]
        top_traders = []
        for entry in top_entries:
            if entry.user_id == request.user.id:
                continue
            try:
                demo_portfolio = DemoPortfolio.objects.get(user=entry.user)
                pdata = calculate_portfolio_data(demo_portfolio)
                perf = pdata.get('total_pnl_percent', 0.0)
            except DemoPortfolio.DoesNotExist:
                perf = 0.0
            top_traders.append({
                'user_id': entry.user_id,
                'username': entry.user.username,
                'score': entry.total_score,
                'streak': entry.current_streak,
                'portfolio_return_percent': round(float(perf), 2),
                'is_followed': entry.user_id in followed_ids,
            })

        feed_query = TradeRationalePost.objects.select_related('author').all()
        feed_items = feed_query[:30]
        feed = [
            {
                'id': post.id,
                'username': post.author.username,
                'author_id': post.author_id,
                'symbol': post.symbol,
                'action': post.action,
                'rationale': post.rationale,
                'created_at': post.created_at.isoformat(),
                'is_following_author': post.author_id in followed_ids,
            }
            for post in feed_items
        ]

        return Response({
            'top_traders': top_traders,
            'feed': feed,
            'following_count': len(followed_ids),
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def follow_copy_trader(request):
    """Follow or unfollow another trader."""
    try:
        followed_user_id = request.data.get('user_id')
        follow = bool(request.data.get('follow', True))
        if not followed_user_id:
            return Response({'error': 'user_id is required'}, status=400)

        try:
            followed_user_id = int(followed_user_id)
        except (TypeError, ValueError):
            return Response({'error': 'user_id must be an integer'}, status=400)

        if followed_user_id == request.user.id:
            return Response({'error': 'You cannot follow yourself'}, status=400)

        target_user = ChallengeLeaderboard.objects.filter(user_id=followed_user_id).first()
        if not target_user:
            return Response({'error': 'Target trader not found'}, status=404)

        if follow:
            PortfolioFollow.objects.get_or_create(follower=request.user, followed_user_id=followed_user_id)
            is_followed = True
        else:
            PortfolioFollow.objects.filter(follower=request.user, followed_user_id=followed_user_id).delete()
            is_followed = False

        return Response({'success': True, 'is_followed': is_followed})
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def post_trade_rationale(request):
    """Create a short rationale post for social learning feed."""
    try:
        symbol = (request.data.get('symbol') or '').strip().upper()
        action = (request.data.get('action') or '').strip().upper()
        rationale = (request.data.get('rationale') or '').strip()

        if not symbol:
            return Response({'error': 'symbol is required'}, status=400)
        if action not in {'BUY', 'SELL', 'HOLD'}:
            return Response({'error': 'action must be BUY, SELL, or HOLD'}, status=400)
        if not rationale:
            return Response({'error': 'rationale is required'}, status=400)
        if len(rationale) > 140:
            return Response({'error': 'rationale must be 140 characters or less'}, status=400)

        post = TradeRationalePost.objects.create(
            author=request.user,
            symbol=symbol,
            action=action,
            rationale=rationale,
        )
        return Response({
            'success': True,
            'post': {
                'id': post.id,
                'username': request.user.username,
                'symbol': post.symbol,
                'action': post.action,
                'rationale': post.rationale,
                'created_at': post.created_at.isoformat(),
            },
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)

