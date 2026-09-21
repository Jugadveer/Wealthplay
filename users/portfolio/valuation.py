"""Portfolio arithmetic: what a set of holdings is worth, and how it got there.

Money is handled as ``Decimal`` throughout and only converted to ``float`` at
the serialisation boundary.
"""

from __future__ import annotations

import logging
from decimal import Decimal

from django.utils import timezone

from . import pricing

logger = logging.getLogger(__name__)

STARTING_BALANCE = Decimal('50000.00')
MAX_SNAPSHOTS = 365


def value_portfolio(portfolio) -> dict:
    """Value every holding and roll it up.

    Returns INR throughout -- a portfolio holding both AAPL and RELIANCE cannot
    be totalled otherwise. Each holding keeps its ``quote_currency`` so the UI
    can still show the native price where that is the honest thing to display.
    """
    holdings = portfolio.holdings if isinstance(portfolio.holdings, dict) else {}
    rate = pricing.usd_to_inr()

    rows, invested, current = [], Decimal('0'), Decimal('0')

    for symbol, position in holdings.items():
        row = _value_holding(symbol, position, rate)
        if row is None:
            continue
        rows.append(row)
        invested += row['_invested']
        current += row['_current']

    for row in rows:
        del row['_invested'], row['_current']

    balance = Decimal(str(portfolio.balance))
    pnl = current - invested

    return {
        'balance': float(balance),
        'invested': float(invested),
        'current_value': float(current),
        'total_value': float(balance + current),
        'total_pnl': float(pnl),
        'total_pnl_percent': float(pnl / invested * 100) if invested > 0 else 0.0,
        'holdings': rows,
        'holdings_count': len(rows),
    }


def _value_holding(symbol: str, position, rate: Decimal) -> dict | None:
    """Value one position, or ``None`` if the row is unusable."""
    if not isinstance(position, dict):
        return None

    try:
        quantity = Decimal(str(position.get('quantity', 0)))
        avg_price = Decimal(str(position.get('avg_price', 0)))
    except (TypeError, ValueError):
        logger.warning('unparsable holding for %s: %r', symbol, position)
        return None

    if quantity <= 0 or avg_price <= 0:
        return None

    quote = pricing.quote(symbol)
    currency = (quote.get('currency') or 'INR').upper()

    # A provider outage returns price 0. Falling back to the buy price shows a
    # flat position rather than a fabricated 100% loss.
    live_price = Decimal(str(quote.get('price') or 0)) or avg_price

    avg_inr = pricing.to_inr(avg_price, currency, rate)
    price_inr = pricing.to_inr(live_price, currency, rate)

    invested = quantity * avg_inr
    current = quantity * price_inr
    pnl = current - invested

    return {
        'symbol': symbol,
        'name': quote.get('name', symbol),
        'quantity': float(quantity),
        'avg_price': float(avg_inr),
        'current_price': float(price_inr),
        'invested': float(invested),
        'current_value': float(current),
        'pnl': float(pnl),
        'pnl_percent': float(pnl / invested * 100) if invested > 0 else 0.0,
        'change_percent': quote.get('change_percent', 0.0),
        'sector': quote.get('sector', 'Unknown'),
        'category': quote.get('category', 'Unknown'),
        'currency': 'INR',
        'quote_currency': currency,
        'native_price': float(live_price),
        'fx_rate': float(rate if currency == 'USD' else 1),
        'is_simulated': quote.get('simulated', False),
        # Stripped by the caller after totalling.
        '_invested': invested,
        '_current': current,
    }


def record_snapshot(portfolio) -> None:
    """Append a point to the portfolio's value history.

    Called after every trade. Without this the value chart has nothing to draw
    but a single dot, which is what the dashboard used to show.
    """
    history = portfolio.trade_history if isinstance(portfolio.trade_history, list) else []

    if not history:
        opened = portfolio.created_at or timezone.now()
        history.append(
            {
                'timestamp': opened.isoformat(),
                'portfolio_value': float(STARTING_BALANCE),
                'invested_value': 0.0,
                'profit_value': 0.0,
            }
        )

    snapshot = value_portfolio(portfolio)
    history.append(
        {
            'timestamp': timezone.now().isoformat(),
            'portfolio_value': snapshot['total_value'],
            'invested_value': snapshot['invested'],
            'profit_value': snapshot['total_pnl'],
        }
    )

    portfolio.trade_history = history[-MAX_SNAPSHOTS:]


def read_history(portfolio, days: int = 30) -> list[dict]:
    """Value history, oldest first, normalised for charting."""
    raw = portfolio.trade_history if isinstance(portfolio.trade_history, list) else []

    points = []
    for entry in raw:
        timestamp = entry.get('timestamp') or entry.get('date')
        if not timestamp:
            continue
        points.append(
            {
                'timestamp': timestamp,
                'portfolio_value': float(entry.get('portfolio_value') or 0),
                'invested_value': float(entry.get('invested_value') or 0),
                'profit_value': float(entry.get('profit_value') or 0),
            }
        )

    points.sort(key=lambda p: p['timestamp'])

    if points:
        return points[-days:]

    # No trades yet: one point at account opening. The chart renders this as a
    # flat baseline rather than a meaningless single dot on a 0-100 axis.
    opened = portfolio.created_at or timezone.now()
    return [
        {
            'timestamp': opened.isoformat(),
            'portfolio_value': float(portfolio.balance),
            'invested_value': 0.0,
            'profit_value': 0.0,
        }
    ]
