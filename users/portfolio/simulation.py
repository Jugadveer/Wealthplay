"""Daily price movement for the fictional practice stocks.

Advancing prices is a scheduled job, not something a page view triggers. Doing
it per-request made prices jitter every time the user refreshed, which taught
the wrong lesson about how markets move.
"""

from __future__ import annotations

import random
from datetime import timedelta

from django.utils import timezone

from users.models import CustomStock
from users.simulator_engine import simulate_stock_movement

SEED_DAYS = 30
MAX_HISTORY = 120


def advance_all() -> int:
    """Move every simulated stock forward one session. Returns how many moved."""
    today = timezone.now().date()
    moved = 0

    for stock in CustomStock.objects.all():
        history = stock.price_history if isinstance(stock.price_history, list) else []

        if not history:
            history = _seed_history(stock, today)

        if stock.last_updated.date() >= today:
            stock.price_history = history[-MAX_HISTORY:]
            stock.save(update_fields=['price_history'])
            continue

        previous = float(stock.current_price)
        new_price, change_percent = simulate_stock_movement(stock)

        stock.current_price = new_price
        stock.change_percent = change_percent
        history.append(_bar(today, previous, float(new_price)))
        stock.price_history = history[-MAX_HISTORY:]
        stock.save()
        moved += 1

    return moved


def _seed_history(stock, today) -> list[dict]:
    """Back-fill a plausible chart so a new stock is not a flat line.

    Seeded from the symbol so the same stock always gets the same history rather
    than regenerating differently on each deploy.
    """
    rng = random.Random(stock.symbol)
    base = float(stock.base_price)
    volatility = float(stock.volatility or 0.02)

    bars = []
    for offset in range(SEED_DAYS, 0, -1):
        day = today - timedelta(days=offset)
        open_price = base * (1 + rng.gauss(0, volatility))
        close_price = base * (1 + rng.gauss(0, volatility))
        bars.append(_bar(day, open_price, close_price, rng))

    return bars


def _bar(day, open_price: float, close_price: float, rng: random.Random | None = None) -> dict:
    """One OHLC bar. Highs and lows are derived so candles are always valid."""
    rng = rng or random
    spread = abs(close_price - open_price) * 0.4 + close_price * 0.004

    return {
        'date': day.isoformat(),
        'open': round(open_price, 2),
        'close': round(close_price, 2),
        'price': round(close_price, 2),
        'high': round(max(open_price, close_price) + rng.uniform(0, spread), 2),
        'low': round(min(open_price, close_price) - rng.uniform(0, spread), 2),
        'volume': rng.randint(80_000, 900_000),
    }
