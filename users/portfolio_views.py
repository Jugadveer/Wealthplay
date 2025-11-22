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

from .models import UserProfile, DemoPortfolio


# Sample stock data - in production, this would come from an external API
SAMPLE_STOCKS = [
    {
        'symbol': 'RELIANCE',
        'name': 'Reliance Industries Ltd',
        'current_price': 2456.50,
        'change_percent': 1.25,
        'category': 'Large Cap',
        'sector': 'Energy',
        'market_cap': '₹16.5L Cr',
    },
    {
        'symbol': 'TCS',
        'name': 'Tata Consultancy Services',
        'current_price': 3521.00,
        'change_percent': -0.75,
        'category': 'Large Cap',
        'sector': 'IT',
        'market_cap': '₹12.8L Cr',
    },
    {
        'symbol': 'HDFCBANK',
        'name': 'HDFC Bank Ltd',
        'current_price': 1658.75,
        'change_percent': 0.50,
        'category': 'Large Cap',
        'sector': 'Banking',
        'market_cap': '₹12.1L Cr',
    },
    {
        'symbol': 'INFY',
        'name': 'Infosys Ltd',
        'current_price': 1523.25,
        'change_percent': 1.10,
        'category': 'Large Cap',
        'sector': 'IT',
        'market_cap': '₹6.3L Cr',
    },
    {
        'symbol': 'HINDUNILVR',
        'name': 'Hindustan Unilever Ltd',
        'current_price': 2489.00,
        'change_percent': -0.25,
        'category': 'Large Cap',
        'sector': 'FMCG',
        'market_cap': '₹5.8L Cr',
    },
    {
        'symbol': 'ICICIBANK',
        'name': 'ICICI Bank Ltd',
        'current_price': 1098.50,
        'change_percent': 0.80,
        'category': 'Large Cap',
        'sector': 'Banking',
        'market_cap': '₹7.7L Cr',
    },
    {
        'symbol': 'SBIN',
        'name': 'State Bank of India',
        'current_price': 724.75,
        'change_percent': 0.60,
        'category': 'Large Cap',
        'sector': 'Banking',
        'market_cap': '₹6.5L Cr',
    },
    {
        'symbol': 'BHARTIARTL',
        'name': 'Bharti Airtel Ltd',
        'current_price': 1245.00,
        'change_percent': 1.50,
        'category': 'Large Cap',
        'sector': 'Telecom',
        'market_cap': '₹6.9L Cr',
    },
    {
        'symbol': 'ITC',
        'name': 'ITC Ltd',
        'current_price': 456.25,
        'change_percent': -0.40,
        'category': 'Large Cap',
        'sector': 'FMCG',
        'market_cap': '₹5.7L Cr',
    },
    {
        'symbol': 'LTIM',
        'name': 'LTI Mindtree Ltd',
        'current_price': 5234.00,
        'change_percent': 2.10,
        'category': 'Mid Cap',
        'sector': 'IT',
        'market_cap': '₹1.2L Cr',
    },
]


def get_stock_price(symbol):
    """Get current price for a stock - in production, this would fetch from API"""
    stock = next((s for s in SAMPLE_STOCKS if s['symbol'] == symbol), None)
    if stock:
        # Add some random variation to simulate price movement
        base_price = stock['current_price']
        variation = base_price * 0.02 * random.uniform(-1, 1) / 100  # ±1% variation
        return round(base_price + variation, 2)
    return 0


def generate_price_history(symbol, days=30):
    """Generate price history for a stock - in production, fetch from API"""
    stock = next((s for s in SAMPLE_STOCKS if s['symbol'] == symbol), None)
    if not stock:
        return []
    
    base_price = stock['current_price']
    history = []
    current_price = base_price
    
    for i in range(days - 1, -1, -1):
        # Simulate price movement with random walk
        change = current_price * random.uniform(-0.03, 0.03)
        current_price = max(current_price + change, base_price * 0.7)  # Don't drop too low
        
        date = (timezone.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        history.append({
            'date': date,
            'price': round(current_price, 2),
            'volume': random.randint(1000000, 10000000)
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
            
            invested = quantity * avg_price
            current_value = quantity * current_price
            pnl = current_value - invested
            pnl_percent = (pnl / invested * 100) if invested > 0 else 0
            
            total_invested += invested
            total_current_value += current_value
            
            stock_info = next((s for s in SAMPLE_STOCKS if s['symbol'] == symbol), None)
            
            holdings_list.append({
                'symbol': symbol,
                'name': stock_info['name'] if stock_info else symbol,
                'quantity': float(quantity),
                'avg_price': float(avg_price),
                'current_price': float(current_price),
                'invested': float(invested),
                'current_value': float(current_value),
                'pnl': float(pnl),
                'pnl_percent': float(pnl_percent),
                'change_percent': stock_info['change_percent'] if stock_info else 0,
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
    """Get available stocks for trading"""
    try:
        # In production, fetch from external API
        stocks = []
        for stock in SAMPLE_STOCKS:
            stocks.append({
                **stock,
                'current_price': get_stock_price(stock['symbol']),
            })
        return Response({'stocks': stocks})
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_stock_detail(request, symbol):
    """Get detailed information about a stock"""
    try:
        stock = next((s for s in SAMPLE_STOCKS if s['symbol'] == symbol), None)
        if not stock:
            return Response({'error': 'Stock not found'}, status=404)
        
        current_price = get_stock_price(symbol)
        price_history = generate_price_history(symbol, 30)
        
        # Check if user owns this stock
        portfolio, _ = DemoPortfolio.objects.get_or_create(
            user=request.user,
            defaults={'balance': 50000.00, 'holdings': {}, 'total_value': 50000.00}
        )
        holdings = portfolio.holdings or {}
        holding = holdings.get(symbol, {})
        
        return Response({
            **stock,
            'current_price': current_price,
            'price_history': price_history,
            'holding': {
                'quantity': holding.get('quantity', 0),
                'avg_price': holding.get('avg_price', 0),
                'invested': holding.get('quantity', 0) * holding.get('avg_price', 0),
            } if holding else None,
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def buy_stock(request):
    """Buy stock in demo portfolio"""
    try:
        symbol = request.data.get('symbol')
        quantity = int(request.data.get('quantity', 0))
        
        if not symbol or quantity <= 0:
            return Response({'error': 'Invalid symbol or quantity'}, status=400)
        
        current_price = get_stock_price(symbol)
        if current_price <= 0:
            return Response({'error': 'Stock not found'}, status=404)
        
        total_cost = Decimal(str(current_price)) * Decimal(str(quantity))
        
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
        
        # Calculate and return updated portfolio data
        portfolio_data = calculate_portfolio_data(portfolio)
        portfolio_data['success'] = True
        portfolio_data['message'] = f'Successfully bought {quantity} shares of {symbol}'
        
        return Response(portfolio_data)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sell_stock(request):
    """Sell stock from demo portfolio"""
    try:
        symbol = request.data.get('symbol')
        quantity = int(request.data.get('quantity', 0))
        
        if not symbol or quantity <= 0:
            return Response({'error': 'Invalid symbol or quantity'}, status=400)
        
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
        
        sale_amount = Decimal(str(current_price)) * Decimal(str(quantity))
        portfolio.holdings = holdings
        # Ensure both sides are Decimal for addition
        if not isinstance(portfolio.balance, Decimal):
            portfolio.balance = Decimal(str(portfolio.balance))
        portfolio.balance = Decimal(str(portfolio.balance)) + sale_amount
        portfolio.save()
        
        # Calculate and return updated portfolio data
        portfolio_data = calculate_portfolio_data(portfolio)
        portfolio_data['success'] = True
        portfolio_data['message'] = f'Successfully sold {quantity} shares of {symbol}'
        
        return Response(portfolio_data)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_portfolio_history(request):
    """Get portfolio value history for charts"""
    try:
        # Generate portfolio history (in production, store and retrieve from DB)
        days = int(request.query_params.get('days', 30))
        portfolio, _ = DemoPortfolio.objects.get_or_create(
            user=request.user,
            defaults={'balance': 50000.00, 'holdings': {}, 'total_value': 50000.00}
        )
        
        history = []
        base_value = float(portfolio.balance)
        holdings = portfolio.holdings or {}
        
        for i in range(days - 1, -1, -1):
            # Simulate portfolio value changes
            change_percent = random.uniform(-0.02, 0.02)
            current_value = base_value * (1 + change_percent * i / days)
            
            date = (timezone.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            history.append({
                'date': date,
                'value': round(current_value, 2),
            })
        
        return Response({'history': history})
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_ai_recommendation(request):
    """Get AI recommendation for stocks - integrates with external model"""
    try:
        symbol = request.data.get('symbol')
        action = request.data.get('action', 'analyze')  # 'analyze', 'buy', 'sell'
        
        if not symbol:
            return Response({'error': 'Symbol required'}, status=400)
        
        stock = next((s for s in SAMPLE_STOCKS if s['symbol'] == symbol), None)
        if not stock:
            return Response({'error': 'Stock not found'}, status=404)
        
        # In production, call the AI model from the GitHub repo
        # For now, generate a sample recommendation
        recommendation_score = random.uniform(0.5, 1.0)
        
        recommendations = {
            'buy': 'Strong buy recommendation',
            'hold': 'Hold position',
            'sell': 'Consider selling'
        }
        
        if recommendation_score >= 0.7:
            recommendation = 'buy'
            confidence = recommendation_score
        elif recommendation_score >= 0.5:
            recommendation = 'hold'
            confidence = recommendation_score
        else:
            recommendation = 'sell'
            confidence = 1 - recommendation_score
        
        return Response({
            'symbol': symbol,
            'recommendation': recommendation,
            'confidence': round(confidence, 2),
            'message': f"AI Analysis: {recommendations[recommendation]} for {stock['name']}. Confidence: {round(confidence * 100)}%",
            'reasons': [
                'Strong financial performance',
                'Positive market sentiment',
                'Good growth prospects',
            ] if recommendation == 'buy' else [
                'Moderate performance',
                'Wait for better entry point',
            ],
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)

