"""
The price engine for the fictional practice stocks.

Three things make this behave like a market rather than a random walk per name.

**A common factor.** Every stock shares one market return for the day, scaled by
its own beta. That is why a bad day is a bad day for most of the book at once —
independent walks never produce the correlation that makes diversification worth
teaching.

**A sector factor.** Names in the same sector share a second, smaller shock, so
the two cybersecurity listings move together more than either moves with energy.
Concentration risk is only a real lesson if concentrated books actually hurt.

**Determinism.** Every return is drawn from a generator seeded on
``(symbol, date)``, so the path for any given day is fixed no matter who
computes it or when. That is what lets prices catch up lazily on read instead of
depending on a scheduler nobody is running — the series is identical either way.

Weekends are skipped, because a market that ticks on Sunday teaches a wrong
thing about when prices are made.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date, timedelta

from django.utils import timezone

from users.models import CustomStock

SEED_DAYS = 90
MAX_HISTORY = 260

# A single session can move a lot, but not without limit: circuit breakers are
# real, and a 90% day would make the chart unreadable and the lesson wrong.
MAX_DAILY_MOVE = 0.18

# How far back a lazy catch-up will walk in one request. A stock untouched for
# longer is back-filled from scratch rather than stepped, which is cheaper.
MAX_CATCH_UP_DAYS = 40


@dataclass(frozen=True)
class Profile:
    """How one kind of stock behaves in a session."""

    drift: float  # expected daily return before any shock
    vol: float  # idiosyncratic daily volatility
    beta: float  # sensitivity to the market factor
    sector_beta: float  # sensitivity to its sector's factor
    reversion: float = 0.0  # pull back towards base_price, per day
    jump_chance: float = 0.0
    jump_size: float = 0.0


# Calibrated so that, annualised, a stable name drifts ~8% with ~12% volatility
# and a speculative one is wild enough to punish concentration.
PROFILES: dict[str, Profile] = {
    'stable': Profile(drift=0.00030, vol=0.007, beta=0.85, sector_beta=0.6, reversion=0.010),
    'dividend': Profile(drift=0.00026, vol=0.006, beta=0.70, sector_beta=0.5, reversion=0.012),
    'growth': Profile(drift=0.00060, vol=0.018, beta=1.25, sector_beta=0.9),
    'tech': Profile(drift=0.00050, vol=0.016, beta=1.30, sector_beta=1.1),
    'finance': Profile(drift=0.00030, vol=0.011, beta=1.10, sector_beta=1.0),
    'energy': Profile(drift=0.00020, vol=0.014, beta=0.95, sector_beta=1.2),
    'volatile': Profile(
        drift=0.00020, vol=0.030, beta=1.45, sector_beta=0.8, jump_chance=0.04, jump_size=0.11
    ),
    'penny': Profile(
        drift=-0.00010, vol=0.040, beta=1.30, sector_beta=0.6, jump_chance=0.06, jump_size=0.16
    ),
}

DEFAULT_PROFILE = PROFILES['stable']


def _rng(*parts) -> random.Random:
    return random.Random('wealthplay:' + ':'.join(str(part) for part in parts))


def is_trading_day(day: date) -> bool:
    """Weekdays only. Holidays are not modelled; the lesson does not need them."""
    return day.weekday() < 5


def previous_trading_day(day: date) -> date:
    day -= timedelta(days=1)
    while not is_trading_day(day):
        day -= timedelta(days=1)
    return day


def market_return(day: date) -> float:
    """The whole simulated market's return for one session.

    Fat-tailed on purpose: a normal draw never produces the days that actually
    teach people what risk feels like.
    """
    rng = _rng('market', day.isoformat())
    shock = rng.gauss(0.0004, 0.0085)
    if rng.random() < 0.03:
        shock += rng.uniform(-0.045, 0.035)
    return shock


def sector_return(sector: str, day: date) -> float:
    """A sector's own shock, on top of the market's."""
    return _rng('sector', (sector or 'General').lower(), day.isoformat()).gauss(0, 0.0055)


def daily_return(stock, day: date, price: float) -> float:
    """One session's return for one stock. Deterministic in ``(symbol, day)``."""
    profile = PROFILES.get(stock.stock_type, DEFAULT_PROFILE)
    rng = _rng('stock', stock.symbol, day.isoformat())

    move = (
        profile.drift
        + profile.beta * market_return(day)
        + profile.sector_beta * sector_return(stock.sector, day)
        + rng.gauss(0, profile.vol)
    )

    # Defensive names are pulled back towards where they started, which is what
    # keeps a "stable" stock stable over years rather than drifting off.
    if profile.reversion and price > 0:
        base = float(stock.base_price or price)
        move += profile.reversion * (base - price) / price

    if profile.jump_chance and rng.random() < profile.jump_chance:
        move += rng.uniform(-profile.jump_size, profile.jump_size)

    strength = float(stock.trend_strength or 0.0)
    if stock.trend == 'bullish':
        move += strength * 0.004
    elif stock.trend == 'bearish':
        move -= strength * 0.004

    return max(-MAX_DAILY_MOVE, min(MAX_DAILY_MOVE, move))


# --------------------------------------------------------------------------- #
# Advancing                                                                    #
# --------------------------------------------------------------------------- #

def advance_all(today: date | None = None) -> int:
    """Bring every simulated stock up to today. Returns how many actually moved."""
    today = today or timezone.localdate()
    return sum(1 for stock in CustomStock.objects.all() if advance(stock, today))


def advance(stock, today: date | None = None) -> bool:
    """Step one stock forward to ``today``, session by session.

    Safe to call from anywhere and as often as you like: a stock already current
    does nothing, and because each session's return is seeded on the date, two
    callers racing produce the same series.
    """
    today = today or timezone.localdate()
    history = stock.price_history if isinstance(stock.price_history, list) else []

    last = _last_bar_date(history)
    if last is None or (today - last).days > MAX_CATCH_UP_DAYS:
        history = _build_history(stock, today)
        _apply(stock, history)
        return True

    missing = []
    cursor = last
    while cursor < today:
        cursor += timedelta(days=1)
        if is_trading_day(cursor):
            missing.append(cursor)

    if not missing:
        return False

    price = float(history[-1]['close'])
    for day in missing:
        price = _append_session(history, stock, day, price)

    _apply(stock, history)
    return True


def _apply(stock, history: list[dict]) -> None:
    history = history[-MAX_HISTORY:]
    last = history[-1]

    stock.price_history = history
    stock.current_price = last['close']
    stock.change_percent = round((last['close'] / last['open'] - 1) * 100, 2)
    stock.save(update_fields=['price_history', 'current_price', 'change_percent', 'last_updated'])


def _last_bar_date(history: list[dict]) -> date | None:
    if not history:
        return None
    try:
        return date.fromisoformat(str(history[-1]['date'])[:10])
    except (KeyError, ValueError):
        return None


def _build_history(stock, today: date) -> list[dict]:
    """Walk the stock from its base price up to today, one session at a time.

    Back-filling with the same generator the live path uses means a new stock's
    chart and its future are drawn from one model, rather than a random history
    stitched onto a different simulation.
    """
    days = [
        today - timedelta(days=offset)
        for offset in range(SEED_DAYS, -1, -1)
        if is_trading_day(today - timedelta(days=offset))
    ]

    history: list[dict] = []
    price = float(stock.base_price or stock.current_price or 100)

    for day in days:
        price = _append_session(history, stock, day, price)

    return history


def _append_session(history: list[dict], stock, day: date, open_price: float) -> float:
    """Append one session and return the close the next one opens at.

    The *rounded* close is carried forward, because that is the number stored
    and therefore the number a later catch-up will read back. Carrying the full
    float instead made the series depend on how often it had been advanced —
    stepping daily and jumping ten days produced prices a paisa apart.
    """
    close_price = max(0.5, open_price * (1 + daily_return(stock, day, open_price)))
    bar = _bar(stock, day, open_price, close_price)
    history.append(bar)
    return bar['close']


def _bar(stock, day: date, open_price: float, close_price: float) -> dict:
    """One OHLC bar. High and low are derived, so a candle is always valid."""
    rng = _rng('bar', stock.symbol, day.isoformat())
    spread = abs(close_price - open_price) * 0.45 + close_price * 0.003

    return {
        'date': day.isoformat(),
        'open': round(open_price, 2),
        'close': round(close_price, 2),
        'price': round(close_price, 2),
        'high': round(max(open_price, close_price) + rng.uniform(0, spread), 2),
        'low': round(max(0.4, min(open_price, close_price) - rng.uniform(0, spread)), 2),
        'volume': rng.randint(80_000, 900_000),
    }
