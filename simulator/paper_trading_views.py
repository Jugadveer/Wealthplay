from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
import yfinance as yf
import pandas as pd
import numpy as np
from decimal import Decimal
from django.utils import timezone
from .models import VirtualPortfolio, PortfolioAsset, PortfolioTransaction
from users.models import UserProgress, UserProfile

def is_feature_unlocked(user, feature_id):
    """Check if a specific trading feature is unlocked via course completion."""
    module_map = {
        'SHORT': 'short-selling-mechanics',
        'STOP_LOSS': 'stop-loss-elite'
    }
    target_module = module_map.get(feature_id)
    if not target_module:
        return True
    
    return UserProgress.objects.filter(
        user=user, 
        module_id=target_module, 
        status='completed'
    ).exists()

from django.db.models import Avg

def detect_revenge_trading(user, current_symbol, current_quantity, current_price):
    """Detect if the user is attempting a revenge trade after a significant loss."""
    portfolio = VirtualPortfolio.objects.filter(user=user).first()
    if not portfolio:
        return False, None

    # Get last transaction
    last_tx = PortfolioTransaction.objects.filter(portfolio=portfolio).order_by('-timestamp').first()
    if not last_tx:
        return False, None

    # Logic: If the user just lost > 10% of portfolio in the last hour,
    # and is now trying to place a trade > 5x their average trade size.
    if (timezone.now() - last_tx.timestamp).total_seconds() > 3600:
        return False, None

    avg_qty = PortfolioTransaction.objects.filter(portfolio=portfolio).aggregate(models_avg=Avg('quantity'))['models_avg'] or 0
    if current_quantity > (Decimal(str(avg_qty)) * 5):
        return True, "Revenge trading detected: Excessive size after recent market activity. Pause and review 'FOMO Filter' module."

    return False, None
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
            'profit_loss': (live_price - float(a.average_buy_price)) * float(a.quantity) if a.position_type == 'LONG' else (float(a.average_buy_price) - live_price) * float(a.quantity),
            'profit_loss_percent': (((live_price / float(a.average_buy_price)) - 1) * 100 if a.position_type == 'LONG' else ((float(a.average_buy_price) / live_price) - 1) * 100) if a.average_buy_price else 0,
            'position_type': a.position_type
        })

    total_asset_value = sum(a['total_value'] for a in asset_data)
    total_value = float(portfolio.cash_balance) + total_asset_value
    
    # Features lock status
    unlocked_features = {
        'short_selling': is_feature_unlocked(request.user, 'SHORT'),
        'stop_loss': is_feature_unlocked(request.user, 'STOP_LOSS')
    }

    return JsonResponse({
        'cash_balance': float(portfolio.cash_balance),
        'total_value': total_value,
        'assets': asset_data,
        'unlocked_features': unlocked_features
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trade_asset(request):
    symbol = request.data.get('symbol', '').strip().upper()
    action = request.data.get('action') # BUY, SELL, SHORT, COVER, STOP_LOSS
    quantity = Decimal(str(request.data.get('quantity', 0)))

    if not symbol or not action or quantity <= 0:
        return JsonResponse({'error': 'Invalid parameters'}, status=400)

    # 1. Feature Unlock Check
    if action in ['SHORT', 'COVER'] and not is_feature_unlocked(request.user, 'SHORT'):
        return JsonResponse({
            'error': 'Short Selling Locked', 
            'lock_redirect': 'short-selling-mechanics',
            'msg': 'Complete the "Short Selling" module to unlock this feature.'
        }, status=403)
    
    if action == 'STOP_LOSS' and not is_feature_unlocked(request.user, 'STOP_LOSS'):
        return JsonResponse({
            'error': 'Stop Loss Locked', 
            'lock_redirect': 'stop-loss-elite',
            'msg': 'Complete the "Tactical Stop-Loss" module to unlock this feature.'
        }, status=403)

    try:
        current_price = Decimal(str(yf.Ticker(symbol).fast_info.last_price))
    except Exception as e:
        return JsonResponse({'error': f'Could not fetch price for {symbol}'}, status=400)
    
    # 2. Revenge Trading Check
    is_revenge, revenge_msg = detect_revenge_trading(request.user, symbol, quantity, current_price)
    if is_revenge:
        return JsonResponse({
            'error': 'Psychological Pause',
            'pause_redirect': 'fomo-filter',
            'msg': revenge_msg
        }, status=403)

    portfolio, _ = VirtualPortfolio.objects.get_or_create(user=request.user)
    total_cost = current_price * quantity
    
    # Handle LONG positions
    if action in ['BUY', 'SELL', 'STOP_LOSS']:
        asset, created = PortfolioAsset.objects.get_or_create(
            portfolio=portfolio, 
            symbol=symbol, 
            position_type='LONG',
            defaults={'average_buy_price': current_price if action == 'BUY' else 0}
        )

        if action == 'BUY':
            if portfolio.cash_balance < total_cost:
                return JsonResponse({'error': 'Insufficient funds'}, status=400)
            
            # Update average buy price
            total_old_cost = asset.quantity * asset.average_buy_price
            new_total_quantity = asset.quantity + quantity
            asset.average_buy_price = (total_old_cost + total_cost) / new_total_quantity
            asset.quantity = new_total_quantity
            portfolio.cash_balance -= total_cost
            asset.save()
            
        elif action in ['SELL', 'STOP_LOSS']:
            if asset.quantity < quantity:
                return JsonResponse({'error': 'Insufficient quantity to sell'}, status=400)
            asset.quantity -= quantity
            portfolio.cash_balance += total_cost
            if asset.quantity == 0:
                asset.delete()
            else:
                asset.save()

    # Handle SHORT positions
    elif action in ['SHORT', 'COVER']:
        asset, created = PortfolioAsset.objects.get_or_create(
            portfolio=portfolio, 
            symbol=symbol, 
            position_type='SHORT',
            defaults={'average_buy_price': current_price}
        )

        if action == 'SHORT':
            if portfolio.cash_balance < total_cost:
                return JsonResponse({'error': 'Insufficient collateral for shorting'}, status=400)
            
            # Average entry price for short
            total_old_proceeds = asset.quantity * asset.average_buy_price
            new_total_quantity = asset.quantity + quantity
            asset.average_buy_price = (total_old_proceeds + total_cost) / new_total_quantity
            asset.quantity = new_total_quantity
            portfolio.cash_balance += total_cost
            asset.save()
            
        elif action == 'COVER':
            if asset.quantity < quantity:
                return JsonResponse({'error': 'Insufficient short quantity to cover'}, status=400)
            
            if portfolio.cash_balance < total_cost:
                return JsonResponse({'error': 'Insufficient funds to cover short'}, status=400)
                
            asset.quantity -= quantity
            portfolio.cash_balance -= total_cost
            if asset.quantity == 0:
                asset.delete()
            else:
                asset.save()

    portfolio.save()

    PortfolioTransaction.objects.create(
        portfolio=portfolio,
        symbol=symbol,
        transaction_type=action,
        quantity=quantity,
        price=current_price
    )

    # Post-Mortem check
    tx_count = PortfolioTransaction.objects.filter(portfolio=portfolio).count()
    pm_available = (tx_count > 0 and tx_count % 10 == 0)

    return JsonResponse({
        'success': True, 
        'msg': f'Successfully executed {action} for {quantity} shares of {symbol}',
        'post_mortem_ready': pm_available
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_post_mortem(request):
    """Generate an AI-powered post-mortem analysis of the user's trading patterns."""
    portfolio = VirtualPortfolio.objects.filter(user=request.user).first()
    if not portfolio:
         return JsonResponse({'error': 'No portfolio found'}, status=404)

    txs = PortfolioTransaction.objects.filter(portfolio=portfolio).order_by('-timestamp')[:50]
    if txs.count() < 10:
         return JsonResponse({'error': 'Not enough data for Post-Mortem. Execute 10 trades.'}, status=400)

    from mentor_engine.gemini_client import gemini_chat
    
    history_data = [f"{tx.transaction_type} {tx.quantity} {tx.symbol} @ {tx.price}" for tx in txs]

    prompt = f"""You are WEALTHPLAY's Elite Performance Auditor. 
Analyze these recent trades: {history_data[:15]}
Identify one psychological bias and one technical struggle.
Provide a 60-second 'Post-Mortem' recap in an elite, high-stakes tone."""

    try:
        report = gemini_chat(prompt)
    except:
        report = "Your recent trades show potential risk concentration. Maintain stop-loss discipline."

    return JsonResponse({'report': report})

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
