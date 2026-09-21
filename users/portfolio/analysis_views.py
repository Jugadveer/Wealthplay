"""Portfolio analysis endpoints: concentration, coaching and stress testing."""

from __future__ import annotations

import logging
from datetime import date, timedelta

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ai import tutor
from market_data import services

from ..models import CustomStock
from . import insights, pricing
from .valuation import value_portfolio
from .views import _portfolio_for

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_portfolio_analysis(request):
    """Everything the analysis tab renders, in one request.

    This replaces four separate calls the page used to make. Three of those
    fetched data the page then never displayed.
    """
    data = value_portfolio(_portfolio_for(request.user))
    holdings = data['holdings']

    return Response(
        {
            'totals': {
                'invested': data['invested'],
                'current_value': data['current_value'],
                'total_pnl': data['total_pnl'],
                'total_pnl_percent': data['total_pnl_percent'],
                'balance': data['balance'],
            },
            'holdings': holdings,
            'concentration': insights.concentration(holdings),
            'nudge': insights.diversification_nudge(holdings),
            'esg': insights.esg_summary(holdings),
            'review': insights.narrative_review(data),
        }
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def critique_trade_idea(request):
    """React to a learner's stated reason before they place a trade."""
    symbol = (request.data.get('symbol') or '').strip().upper()
    rationale = (request.data.get('rationale') or '').strip()
    action = (request.data.get('action') or 'buy').lower()
    quantity = _positive_int(request.data.get('quantity')) or 1

    if not symbol or not rationale:
        return Response({'error': 'A symbol and a rationale are required.'}, status=400)

    data = value_portfolio(_portfolio_for(request.user))
    quote = pricing.quote(symbol)
    trade_value = quote['price'] * quantity
    total = data['total_value'] or 1

    critique = tutor.critique_trade(
        symbol,
        action=action,
        quantity=quantity,
        rationale=rationale,
        weight_percent=trade_value / total * 100,
    )

    return Response({'available': bool(critique), 'critique': critique})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_hindsight_replay(request):
    """Replay the current holdings through a past market period.

    Answers "what would this portfolio have done in 2008?" using real closes,
    which is a far better risk lesson than a volatility number.
    """
    periods = {
        '2008-crash': (date(2008, 9, 1), date(2009, 6, 30), 'Global credit crisis'),
        '2020-pandemic': (date(2020, 2, 1), date(2020, 9, 1), 'Pandemic shock and recovery'),
        '2022-ratehike': (date(2022, 1, 1), date(2022, 12, 31), 'Inflation and rate-hike cycle'),
    }

    preset = (request.query_params.get('preset') or '2020-pandemic').lower()
    if preset not in periods:
        return Response({'error': f'Unknown period. Choose one of: {", ".join(periods)}.'}, status=400)

    start, end, label = periods[preset]
    portfolio = _portfolio_for(request.user)
    holdings = portfolio.holdings or {}

    if not holdings:
        return Response({'available': False, 'reason': 'Buy something first — there is nothing to replay.'})

    series = _replay_series(holdings, start, end)
    if not series:
        return Response(
            {
                'available': False,
                'reason': 'None of your holdings were trading in this period.',
            }
        )

    values = [point['value'] for point in series]
    peak = running_peak = values[0]
    drawdown = 0.0
    for value in values:
        running_peak = max(running_peak, value)
        drawdown = min(drawdown, (value - running_peak) / running_peak * 100)
        peak = running_peak

    return Response(
        {
            'available': True,
            'period': {'label': label, 'start': start.isoformat(), 'end': end.isoformat()},
            'series': series,
            'summary': {
                'start_value': round(values[0], 2),
                'end_value': round(values[-1], 2),
                'return_percent': round((values[-1] - values[0]) / values[0] * 100, 2),
                'max_drawdown_percent': round(drawdown, 2),
                'peak_value': round(peak, 2),
            },
        }
    )


def _replay_series(holdings: dict, start: date, end: date) -> list[dict]:
    """Daily portfolio value across a historical window.

    Simulated stocks are skipped: they have no real history, so including them
    would invent one.
    """
    import yfinance as yf

    by_date: dict[str, float] = {}
    rate = pricing.usd_to_inr()

    for symbol, position in holdings.items():
        quantity = float(position.get('quantity') or 0)
        if quantity <= 0 or CustomStock.objects.filter(symbol=symbol).exists():
            continue

        try:
            frame = yf.Ticker(services.provider_symbol(symbol)).history(
                start=start.isoformat(),
                end=(end + timedelta(days=1)).isoformat(),
                interval='1d',
            )
        except Exception:
            logger.warning('replay fetch failed for %s', symbol, exc_info=True)
            continue

        if frame.empty:
            continue

        currency = services.currency_for(symbol)
        for index, row in frame.iterrows():
            key = index.date().isoformat()
            close = float(pricing.to_inr(float(row['Close']), currency, rate))
            by_date[key] = by_date.get(key, 0.0) + quantity * close

    return [{'date': key, 'value': round(by_date[key], 2)} for key in sorted(by_date)]


