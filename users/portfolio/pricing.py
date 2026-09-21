"""Prices, currency conversion and the sector profiles used for ESG scoring.

Every quote comes from :mod:`market_data.services`, which owns the cache. This
module only converts and shapes.
"""

from __future__ import annotations

from decimal import Decimal

from django.core.cache import cache

from market_data import services

# Used when the FX provider is unreachable. Wrong by a few percent beats a page
# that cannot render a total.
USD_TO_INR_FALLBACK = Decimal('85')
FX_CACHE_TTL = 60 * 60 * 6


def usd_to_inr() -> Decimal:
    """Current USD/INR rate, cached for six hours."""
    cached = cache.get('fx:usdinr')
    if cached:
        return Decimal(cached)

    quote = services.get_quote('INR=X')
    rate = Decimal(str(quote.price)) if quote.price > 0 else USD_TO_INR_FALLBACK
    cache.set('fx:usdinr', str(rate), FX_CACHE_TTL)
    return rate


def to_inr(amount, currency: str, rate: Decimal | None = None) -> Decimal:
    """Convert to INR. Portfolio totals are always INR so they can be summed."""
    value = Decimal(str(amount or 0))
    if (currency or 'INR').upper() != 'USD':
        return value
    return value * (rate if rate is not None else usd_to_inr())


def quote(symbol: str) -> dict:
    """Quote for one symbol as a plain dict, with an ESG profile attached."""
    q = services.get_quote(symbol)
    profile = sector_profile(q.sector)
    return {
        **q.as_dict(),
        'category': _cap_category(q.market_cap, q.simulated),
        'esg_score': profile['esg_score'],
        'carbon_intensity': profile['carbon_intensity'],
        'esg_tag': profile['tag'],
    }


def price(symbol: str) -> float:
    return services.get_price(symbol)


def history(symbol: str, days: int = 90) -> list[dict]:
    """Daily closes with 20- and 50-session moving averages attached."""
    series = services.get_history(symbol, days)
    return _with_moving_averages(series)


def _cap_category(market_cap, simulated: bool) -> str:
    if simulated:
        return 'Simulated'
    if not market_cap:
        return 'Unknown'
    if market_cap >= 200_000_000_000:
        return 'Mega Cap'
    if market_cap >= 10_000_000_000:
        return 'Large Cap'
    if market_cap >= 2_000_000_000:
        return 'Mid Cap'
    return 'Small Cap'


def _with_moving_averages(series: list[dict]) -> list[dict]:
    """Attach ma20/ma50. Computed here so the provider is not asked twice."""
    closes = [point['close'] for point in series]
    out = []

    for i, point in enumerate(series):
        window20 = closes[max(0, i - 19) : i + 1]
        window50 = closes[max(0, i - 49) : i + 1]
        out.append(
            {
                **point,
                'price': point['close'],
                'ma20': round(sum(window20) / len(window20), 2) if i >= 19 else None,
                'ma50': round(sum(window50) / len(window50), 2) if i >= 49 else None,
            }
        )
    return out


# --------------------------------------------------------------------------- #
# Sector profiles                                                              #
# --------------------------------------------------------------------------- #
# Deliberately coarse. These teach that sector choice carries a carbon and
# governance profile; they are not a substitute for a real ESG rating, and the
# UI labels them as illustrative.

_SECTOR_PROFILES = {
    'technology': (74, 38, 'moderate-footprint'),
    'information technology': (74, 38, 'moderate-footprint'),
    'communication services': (67, 33, 'balanced'),
    'healthcare': (78, 30, 'resilient'),
    'consumer defensive': (72, 35, 'balanced'),
    'financial services': (68, 28, 'balanced'),
    'finance': (68, 28, 'balanced'),
    'real estate': (60, 57, 'improving'),
    'industrials': (58, 63, 'transition-sensitive'),
    'utilities': (56, 70, 'improving'),
    'materials': (52, 74, 'transition-sensitive'),
    'energy': (42, 86, 'high-footprint'),
    'oil & gas': (34, 92, 'high-footprint'),
}

_DEFAULT_PROFILE = (64, 46, 'balanced')


def sector_profile(sector: str | None) -> dict:
    esg, carbon, tag = _SECTOR_PROFILES.get((sector or '').strip().lower(), _DEFAULT_PROFILE)
    return {'esg_score': esg, 'carbon_intensity': carbon, 'tag': tag}
