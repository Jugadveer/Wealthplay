"""
Portfolio API endpoints for demo trading simulator
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import json
import random

# --- UPDATED IMPORTS ---
import yfinance as yf
import pandas as pd
from .ml_predictor import ML_PREDICTOR, TICKERS
# -----------------------

from .models import UserProfile, DemoPortfolio, PredictedStockData


USD_TO_INR_FALLBACK = Decimal('85')


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


# --- REMOVAL: SAMPLE_STOCKS removed, replaced by live data ---


def get_stock_info(symbol, use_cache=True):
    """
    Fetch basic stock info - uses cached data for instant response.
    Falls back to live API if cache is missing or stale.
    Returns prices in appropriate currency (INR for Indian stocks, USD for US stocks).
    """
    # First check if it's a custom stock
    from .models import CustomStock
    try:
        custom_stock = CustomStock.objects.get(symbol=symbol)
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
                }
        except PredictedStockData.DoesNotExist:
            pass  # Fall through to live fetch
    
    # Fallback to live API if cache miss or stale
    full_ticker = ML_PREDICTOR._get_full_ticker(symbol)
    try:
        ticker = yf.Ticker(full_ticker)
        info = ticker.info
        
        name = info.get('longName') or info.get('shortName') or symbol
        sector = info.get('sector') or 'Other'
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
        }
    except Exception as e:
        return {
            'symbol': symbol,
            'name': f"{symbol} (Data Unavailable)",
            'current_price': 0.0,
            'change_percent': 0.0,
            'category': 'Unknown',
            'sector': 'Unknown',
            'market_cap': 'N/A',
            'currency': 'INR' if is_indian_stock else 'USD',
        }


def get_stock_price(symbol):
    """Get current price for a stock - handles both custom and real stocks"""
    from .models import CustomStock
    try:
        custom_stock = CustomStock.objects.get(symbol=symbol)
        return float(custom_stock.current_price)
    except CustomStock.DoesNotExist:
        pass
    info = get_stock_info(symbol)
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
            current_price_val = get_stock_price(symbol)
            if current_price_val <= 0:
                # If stock price not found, use avg_price as fallback
                current_price_val = float(avg_price) if avg_price > 0 else 0
            
            if quantity <= 0 or avg_price <= 0:
                continue
                
            current_price = Decimal(str(current_price_val))
            stock_info = get_stock_info(symbol)
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
            if custom.last_updated.date() < today:
                prev_price = float(custom.current_price)
                new_price, change_pct = simulate_stock_movement(custom)
                custom.current_price = new_price
                custom.change_percent = change_pct
                
                # Update history
                history = custom.price_history if isinstance(custom.price_history, list) else []
                history.append({
                    "date": today.isoformat(),
                    "price": float(custom.current_price),
                    "close": float(custom.current_price),
                    "open": prev_price,
                    "high": max(prev_price, float(custom.current_price)),
                    "low": min(prev_price, float(custom.current_price)),
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
                info = get_stock_info(symbol, use_cache=True)
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
        stock_info = get_stock_info(symbol, use_cache=False)
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
        
        stock_info = get_stock_info(symbol)
        current_price = get_stock_price(symbol)
        if current_price <= 0:
            print(f"Error: Price for {symbol} returned 0.0 or failed fetch.")
            return Response({'error': f'Stock {symbol} not found or price unavailable'}, status=404)

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
        
        stock_info = get_stock_info(symbol)
        current_price = get_stock_price(symbol)
        if current_price <= 0:
            return Response({'error': 'Stock not found'}, status=404)
        
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
                    'is_custom': False
                })
        except PredictedStockData.DoesNotExist:
            pass  # Fall through to live prediction
        
        # Fallback to live prediction if cache miss
        stock_info = get_stock_info(symbol, use_cache=False)
        if stock_info.get('current_price', 0.0) <= 0.0:
            return Response({'error': 'Stock data not available for AI analysis'}, status=404)
        
        # Run the actual ML prediction
        prediction_results = ML_PREDICTOR.predict(symbol)
        
        recommendation = prediction_results['direction']
        confidence = prediction_results['confidence']
        regime = prediction_results['regime']
        vol = prediction_results['vol']
        
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
        
        reasons = [
            f'Market Regime: Currently **{regime}** (Volatility: {round(vol * 100, 2)}%)',
            f'Confidence Level: {round(confidence * 100)}%',
            f'Predicted Action: {action_text}.'
        ]
        
        return Response({
            'symbol': symbol,
            'recommendation': recommendation,
            'confidence': round(confidence, 2),
            'message': message,
            'reasons': reasons,
            'metadata': {
                'regime': regime,
                'volatility': round(vol, 4)
            }
        })
    except Exception as e:
        import traceback
        print(f"Error in get_ai_recommendation: {e}")
        print(traceback.format_exc())
        return Response({'error': str(e)}, status=500)

