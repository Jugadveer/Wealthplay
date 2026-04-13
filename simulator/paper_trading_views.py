from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
import yfinance as yf
import pandas as pd
import numpy as np
from decimal import Decimal
from .models import VirtualPortfolio, PortfolioAsset, PortfolioTransaction

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_portfolio(request):
    portfolio, _ = VirtualPortfolio.objects.get_or_create(user=request.user)
    assets = portfolio.assets.all()
    
    # Fetch live prices
    symbols = [a.symbol for a in assets]
    current_prices = {}
    if symbols:
        try:
            tickers = yf.Tickers(" ".join(symbols))
            for sym in symbols:
                current_prices[sym] = tickers.tickers[sym].fast_info.last_price
        except Exception:
            pass

    asset_data = []
    for a in assets:
        live_price = current_prices.get(a.symbol, float(a.average_buy_price))
        asset_data.append({
            'symbol': a.symbol,
            'quantity': float(a.quantity),
            'average_buy_price': float(a.average_buy_price),
            'live_price': live_price,
            'total_value': float(a.quantity) * live_price,
            'profit_loss': (live_price - float(a.average_buy_price)) * float(a.quantity),
            'profit_loss_percent': ((live_price / float(a.average_buy_price)) - 1) * 100 if a.average_buy_price else 0
        })

    total_asset_value = sum(a['total_value'] for a in asset_data)
    total_value = float(portfolio.cash_balance) + total_asset_value

    return JsonResponse({
        'cash_balance': float(portfolio.cash_balance),
        'total_value': total_value,
        'assets': asset_data,
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trade_asset(request):
    symbol = request.data.get('symbol', '').strip().upper()
    action = request.data.get('action') # BUY or SELL
    quantity = Decimal(str(request.data.get('quantity', 0)))

    if not symbol or not action or quantity <= 0:
        return JsonResponse({'error': 'Invalid parameters'}, status=400)

    try:
        current_price = Decimal(str(yf.Ticker(symbol).fast_info.last_price))
    except Exception as e:
        return JsonResponse({'error': f'Could not fetch price for {symbol}'}, status=400)
    
    portfolio, _ = VirtualPortfolio.objects.get_or_create(user=request.user)
    total_cost = current_price * quantity
    
    asset, created = PortfolioAsset.objects.get_or_create(portfolio=portfolio, symbol=symbol, defaults={'average_buy_price': 0})

    if action == 'BUY':
        if portfolio.cash_balance < total_cost:
            return JsonResponse({'error': 'Insufficient funds'}, status=400)
        
        # Update average buy price
        total_old_cost = asset.quantity * asset.average_buy_price
        new_total_quantity = asset.quantity + quantity
        asset.average_buy_price = (total_old_cost + total_cost) / new_total_quantity
        asset.quantity = new_total_quantity
        portfolio.cash_balance -= total_cost
        
    elif action == 'SELL':
        if asset.quantity < quantity:
            return JsonResponse({'error': 'Insufficient quantity to sell'}, status=400)
        asset.quantity -= quantity
        portfolio.cash_balance += total_cost
        
    else:
        return JsonResponse({'error': 'Invalid action'}, status=400)

    asset.save()
    portfolio.save()

    PortfolioTransaction.objects.create(
        portfolio=portfolio,
        symbol=symbol,
        transaction_type=action,
        quantity=quantity,
        price=current_price
    )
    
    if asset.quantity == 0:
        asset.delete()

    return JsonResponse({'success': True, 'msg': f'Successfully {action}ed {quantity} shares of {symbol}'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def portfolio_analytics(request):
    portfolio, _ = VirtualPortfolio.objects.get_or_create(user=request.user)
    assets = portfolio.assets.all()
    if not assets:
        return JsonResponse({'error': 'No assets to analyze'}, status=400)
        
    symbols = [a.symbol for a in assets]
    try:
        # Fetch 3mo history for analytics
        df = yf.download(symbols, period="3mo", interval="1d")['Close']
        if not isinstance(df, pd.DataFrame):
            df = pd.DataFrame(df)
            
        returns = df.pct_change().dropna()
        
        # Sharpe ratio (assuming risk free rate = 0.05 / 252)
        mean_ret = returns.mean() * 252
        volatility = returns.std() * np.sqrt(252)
        sharpe = (mean_ret - 0.05) / (volatility + 1e-9)
        
        # Calculate portfolio weights
        current_prices = {sym: df[sym].iloc[-1] for sym in symbols if sym in df}
        total_value = sum(float(a.quantity) * current_prices.get(a.symbol, float(a.average_buy_price)) for a in assets)
        weights = [float(a.quantity) * current_prices.get(a.symbol, float(a.average_buy_price))/total_value for a in assets]
        
        port_ret = np.dot(mean_ret, weights)
        port_vol = np.sqrt(np.dot(weights, np.dot(returns.cov() * 252, weights)))
        port_sharpe = (port_ret - 0.05) / port_vol if port_vol > 0 else 0
        
        # Use Gemini for feedback
        try:
             from mentor_engine.gemini_client import gemini_chat
             
             risk_tol = request.user.userprofile.risk_tolerance if hasattr(request.user, 'userprofile') else 'medium'
             
             prompt = f"""You are WEALTHPLAY — a friendly financial mentor.
Analyze this user's paper trading portfolio:
Holdings: {symbols}
Sharpe Ratio: {port_sharpe:.2f} (measures risk-adjusted return)
Volatility: {port_vol:.2f}
User Risk Tolerance: {risk_tol}
Give 3 bullet points of weekly feedback and suggestions to improve diversification or manage risk."""
             
             review = gemini_chat(prompt)
        except Exception as e:
             review = f"• Your volatility is {port_vol:.2f}.\n• Keep practicing to improve Sharpe Ratio ({port_sharpe:.2f})."

        return JsonResponse({
            'portfolio_return': port_ret,
            'portfolio_volatility': port_vol,
            'portfolio_sharpe': port_sharpe,
            'mentor_review': review
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
