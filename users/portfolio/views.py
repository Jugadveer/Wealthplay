"""Portfolio API endpoints.

Views stay thin: parse, delegate, respond. The arithmetic lives in
:mod:`valuation`, the analysis in :mod:`insights`, and every price comes from
:mod:`market_data.services`, which is the only thing allowed to touch the network.
"""

from __future__ import annotations

import logging
from decimal import Decimal

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from market_data import services

from ..models import CustomStock, DemoPortfolio
from . import insights, pricing
from .valuation import STARTING_BALANCE, read_history, record_snapshot, value_portfolio

logger = logging.getLogger(__name__)

PORTFOLIO_DEFAULTS = {
    'balance': STARTING_BALANCE,
    'holdings': {},
    'total_value': STARTING_BALANCE,
}


def _portfolio_for(user) -> DemoPortfolio:
    portfolio, _ = DemoPortfolio.objects.get_or_create(user=user, defaults=PORTFOLIO_DEFAULTS)
    return portfolio


# --------------------------------------------------------------------------- #
# Reading                                                                      #
# --------------------------------------------------------------------------- #

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_portfolio(request):
    """Current holdings, cash and P&L."""
    return Response(value_portfolio(_portfolio_for(request.user)))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_portfolio_history(request):
    """Value over time for the performance chart."""
    days = max(7, min(365, int(request.query_params.get('days', 30) or 30)))
    return Response({'history': read_history(_portfolio_for(request.user), days)})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_stocks(request):
    """Everything tradable: simulated stocks first, then real listings."""
    stocks = [
        {
            'symbol': stock.symbol,
            'name': stock.name,
            'current_price': float(stock.current_price),
            'change_percent': float(stock.change_percent),
            'category': stock.category,
            'sector': stock.sector,
            'currency': stock.currency or 'INR',
            'is_custom': True,
        }
        for stock in CustomStock.objects.filter(current_price__gt=0).order_by('symbol')
    ]

    for symbol in services.TRACKED_SYMBOLS:
        quote = pricing.quote(symbol)
        if quote['price'] <= 0:
            continue
        stocks.append(
            {
                'symbol': quote['symbol'],
                'name': quote['name'],
                'current_price': quote['price'],
                'change_percent': quote['change_percent'],
                'category': quote['category'],
                'sector': quote['sector'],
                'currency': quote['currency'],
                'is_custom': False,
            }
        )

    return Response({'stocks': stocks})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_stock_detail(request, symbol):
    """One stock: quote, chart series, summary stats and the user's position."""
    symbol = symbol.upper()
    quote = pricing.quote(symbol)

    custom = CustomStock.objects.filter(symbol=symbol).first()
    if custom:
        series = (custom.price_history or [])[-90:]
    else:
        series = pricing.history(symbol, days=90)

    holdings = _portfolio_for(request.user).holdings or {}
    position = holdings.get(symbol)

    # The account settles in INR, so the ticket needs the converted price to
    # compare an order against the cash balance. Showing a dollar order value
    # beside a rupee balance invites a comparison that does not hold.
    price_inr = float(pricing.to_inr(quote['price'], quote['currency']))

    return Response(
        {
            **quote,
            'current_price': quote['price'],
            'price_inr': round(price_inr, 2),
            'is_custom': bool(custom),
            'price_history': series,
            'summary': _series_summary(series, quote['price']),
            'holding': (
                {
                    'quantity': position.get('quantity', 0),
                    'avg_price': float(position.get('avg_price', 0)),
                    'invested': float(position.get('quantity', 0)) * float(position.get('avg_price', 0)),
                }
                if position
                else None
            ),
        }
    )


def _series_summary(series: list[dict], fallback_price: float) -> dict:
    """High/low/average over the visible window."""
    closes = [float(p.get('close') or p.get('price') or 0) for p in series]
    closes = [c for c in closes if c > 0]

    if not closes:
        return {'high': fallback_price, 'low': fallback_price, 'average': fallback_price, 'avg_volume': 0}

    volumes = [int(p.get('volume') or 0) for p in series]
    latest = series[-1]

    return {
        'high': round(max(closes), 2),
        'low': round(min(closes), 2),
        'average': round(sum(closes) / len(closes), 2),
        'avg_volume': round(sum(volumes) / len(volumes)) if volumes else 0,
        'ma20': latest.get('ma20'),
        'ma50': latest.get('ma50'),
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_tickers_info(request):
    """Quotes plus long-horizon returns, used by the goal planner."""
    symbols = [s.strip().upper() for s in request.GET.get('symbols', '').split(',') if s.strip()][:10]
    if not symbols:
        return Response({'results': {}})

    results = {}
    for symbol in symbols:
        quote = pricing.quote(symbol)
        series = services.get_history(symbol, days=365)
        closes = [p['close'] for p in series]

        results[symbol] = {
            **quote,
            'current_price': quote['price'],
            'returns': {
                '1m': _window_return(closes, 21),
                '6m': _window_return(closes, 126),
                '1y': _window_return(closes, 252),
            },
        }

    return Response({'results': results})


def _window_return(closes: list[float], sessions: int) -> float | None:
    """Percentage change over ``sessions``, or ``None`` if the series is too short."""
    if len(closes) <= sessions:
        return None
    start = closes[-sessions]
    return round((closes[-1] - start) / start * 100, 2) if start else None


# --------------------------------------------------------------------------- #
# Trading                                                                      #
# --------------------------------------------------------------------------- #

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def buy_stock(request):
    """Buy shares at the current quote."""
    from ..achievement_views import check_and_unlock_achievements

    symbol = (request.data.get('symbol') or '').strip().upper()
    quantity = _positive_int(request.data.get('quantity'))
    if not symbol or not quantity:
        return Response({'error': 'A symbol and a positive quantity are required.'}, status=400)

    quote = pricing.quote(symbol)
    if quote['price'] <= 0:
        return Response({'error': f'No price available for {symbol} right now. Try again shortly.'}, status=503)

    cost = pricing.to_inr(Decimal(str(quote['price'])) * quantity, quote['currency'])
    portfolio = _portfolio_for(request.user)
    balance = Decimal(str(portfolio.balance))

    if balance < cost:
        return Response(
            {'error': f'Costs ₹{cost:,.2f} but only ₹{balance:,.2f} is available.'},
            status=400,
        )

    holdings = portfolio.holdings or {}
    existing = holdings.get(symbol)

    # The cost basis is stored in the stock's OWN currency, because that is what
    # `valuation` converts from. Storing the INR amount here made the valuer
    # convert a second time, which showed a dollar holding down 98%.
    unit_price = Decimal(str(quote['price']))

    if existing:
        # Weighted average, so the basis reflects every lot bought.
        held = Decimal(str(existing['quantity']))
        basis = Decimal(str(existing['avg_price']))
        total = held + quantity
        holdings[symbol] = {
            'quantity': float(total),
            'avg_price': float((held * basis + unit_price * quantity) / total),
        }
    else:
        holdings[symbol] = {'quantity': quantity, 'avg_price': float(unit_price)}

    portfolio.holdings = holdings
    portfolio.balance = balance - cost
    record_snapshot(portfolio)
    portfolio.save()

    return Response(
        {
            **value_portfolio(portfolio),
            'success': True,
            'message': f'Bought {quantity} {symbol} at {_money(quote)}.',
            'newly_unlocked_achievements': _serialise_unlocks(check_and_unlock_achievements(request.user)),
        }
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sell_stock(request):
    """Sell shares and score the exit for discipline."""
    from ..achievement_views import check_and_unlock_achievements

    symbol = (request.data.get('symbol') or '').strip().upper()
    quantity = _positive_int(request.data.get('quantity'))
    if not symbol or not quantity:
        return Response({'error': 'A symbol and a positive quantity are required.'}, status=400)

    portfolio = _portfolio_for(request.user)
    holdings = portfolio.holdings or {}
    position = holdings.get(symbol)

    if not position or position['quantity'] < quantity:
        held = position['quantity'] if position else 0
        return Response({'error': f'You hold {held:g} {symbol}, so {quantity} cannot be sold.'}, status=400)

    quote = pricing.quote(symbol)
    if quote['price'] <= 0:
        return Response({'error': f'No price available for {symbol} right now. Try again shortly.'}, status=503)

    held_before = float(position['quantity'])
    avg_price = float(position['avg_price'])

    position['quantity'] -= quantity
    if position['quantity'] <= 0:
        del holdings[symbol]

    proceeds = pricing.to_inr(Decimal(str(quote['price'])) * quantity, quote['currency'])
    portfolio.holdings = holdings
    portfolio.balance = Decimal(str(portfolio.balance)) + proceeds
    record_snapshot(portfolio)
    portfolio.save()

    return Response(
        {
            **value_portfolio(portfolio),
            'success': True,
            'message': f'Sold {quantity} {symbol} at {_money(quote)}.',
            # Both prices are in the stock's own currency, matching the price
            # history the score is measured against.
            'sell_discipline': insights.sell_discipline(
                symbol,
                sold=quantity,
                held_before=held_before,
                price=quote['price'],
                avg_price=avg_price,
            ),
            'newly_unlocked_achievements': _serialise_unlocks(check_and_unlock_achievements(request.user)),
        }
    )


def _positive_int(value) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return 0
    return parsed if parsed > 0 else 0


def _money(quote: dict) -> str:
    symbol = '$' if quote['currency'] == 'USD' else '₹'
    return f'{symbol}{quote["price"]:,.2f}'


def _serialise_unlocks(achievements) -> list[dict]:
    return [{'id': a.id, 'name': a.name, 'xp_reward': a.xp_reward} for a in achievements]
