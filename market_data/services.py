"""
The one place the app talks to a market data provider.

Why this exists
---------------
Quotes were previously fetched inline from every view via ``yfinance``. A single
dashboard load issued 44 API calls, and the three slowest -- portfolio, stock
detail, achievements -- each spent over four seconds blocked on network I/O,
because ``yfinance`` needs one ``.info`` call plus two ``.history()`` calls per
symbol. There was a ten-minute database cache, but nothing ever wrote to it, so
it never produced a hit.

The rules here:

* No view calls ``yfinance`` directly. Everything goes through this module.
* Every provider call is wrapped in :func:`_cached`, so a cold symbol costs one
  round trip and every later reader is served from cache.
* A provider failure degrades to stale cache, then to a neutral placeholder. A
  dead upstream must never turn into a 500.
* Simulated (``CustomStock``) symbols never touch the network at all.
"""

from __future__ import annotations

import logging
import math
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta

import yfinance as yf
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Cache lifetimes. Quotes move constantly; company metadata and daily bars do
# not, so they are held far longer to keep the provider call count low.
TTL_QUOTE = 90
TTL_PROFILE = 60 * 60 * 12
TTL_HISTORY = 60 * 30
TTL_NEWS = 60 * 30

# Symbols that need a suffix before the provider recognises them.
NSE_SYMBOLS = frozenset(
    {"RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "ITC", "BHARTIARTL"}
)

TRACKED_SYMBOLS = (
    "AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "META", "NVDA", "SPY",
    *sorted(NSE_SYMBOLS),
)


@dataclass(frozen=True)
class Quote:
    """A price point plus the context needed to render it correctly."""

    symbol: str
    name: str
    price: float
    change_percent: float
    currency: str
    sector: str = "Unknown"
    market_cap: float | None = None
    simulated: bool = False

    def as_dict(self) -> dict:
        return asdict(self)


def currency_for(symbol: str) -> str:
    """Indian listings quote in INR, everything else in USD.

    The app used to render every price with a rupee sign, so Apple showed as
    ``₹302.45``.
    """
    return "INR" if symbol.upper() in NSE_SYMBOLS else "USD"


def provider_symbol(symbol: str) -> str:
    """Map an app symbol to the provider's ticker (``SBIN`` -> ``SBIN.NS``)."""
    upper = symbol.upper()
    return f"{upper}.NS" if upper in NSE_SYMBOLS else upper


def _cached(key: str, ttl: int, producer):
    """Return ``producer()``, memoised under ``key`` for ``ttl`` seconds.

    On provider failure the last known good value is returned -- a stale price
    beats an error page -- and ``None`` only if nothing was ever cached.
    """
    hit = cache.get(key)
    if hit is not None:
        return hit

    try:
        value = producer()
    except Exception:
        logger.warning("market provider failed for %s", key, exc_info=True)
        return cache.get(f"{key}:stale")

    if value is not None:
        cache.set(key, value, ttl)
        # A long-lived copy so a later outage still has something to serve.
        cache.set(f"{key}:stale", value, 60 * 60 * 24 * 7)
    return value


# --------------------------------------------------------------------------- #
# Simulated stocks                                                             #
# --------------------------------------------------------------------------- #

def _simulated_quote(symbol: str) -> Quote | None:
    """Quote for a ``CustomStock``, or ``None`` if the symbol is a real listing.

    Brings the stock up to today before quoting it. Each session's return is
    seeded on ``(symbol, date)``, so advancing here produces exactly the series
    a nightly job would have written — which means the practice market keeps
    moving on a machine where nothing is scheduled.
    """
    from users.models import CustomStock
    from users.portfolio.simulation import advance

    stock = CustomStock.objects.filter(symbol=symbol.upper()).first()
    if stock is None:
        return None

    try:
        advance(stock)
    except Exception:
        logger.warning("could not advance %s", stock.symbol, exc_info=True)

    return Quote(
        symbol=stock.symbol,
        name=stock.name,
        price=float(stock.current_price),
        change_percent=float(stock.change_percent),
        currency=stock.currency or "INR",
        sector=stock.sector or "Simulated",
        simulated=True,
    )


# --------------------------------------------------------------------------- #
# Public API                                                                   #
# --------------------------------------------------------------------------- #

def get_quote(symbol: str) -> Quote:
    """Current quote for one symbol. Always returns; never raises."""
    symbol = symbol.upper()

    simulated = _simulated_quote(symbol)
    if simulated is not None:
        return simulated

    payload = _cached(f"quote:{symbol}", TTL_QUOTE, lambda: _fetch_quote(symbol))
    if payload is None:
        # Unknown symbol or a cold cache during an outage. Render as "no data"
        # rather than a zero price that looks like a real crash to -100%.
        return Quote(symbol, symbol, 0.0, 0.0, currency_for(symbol))
    return Quote(**payload)


def get_quotes(symbols) -> dict[str, Quote]:
    """Quotes for many symbols, keyed by symbol.

    Cached symbols cost nothing, so a portfolio page is one provider call on the
    first load of each holding and zero afterwards.
    """
    return {s.upper(): get_quote(s) for s in dict.fromkeys(s.upper() for s in symbols)}


def get_price(symbol: str) -> float:
    return get_quote(symbol).price


def get_history(symbol: str, days: int = 90) -> list[dict]:
    """Daily closes as ``[{date, close, volume}]``, oldest first.

    Simulated stocks get a deterministic walk seeded from the symbol, so the
    same stock always draws the same chart instead of reshuffling per request.
    """
    symbol = symbol.upper()

    if _simulated_quote(symbol) is not None:
        return _simulated_history(symbol, days)

    return _cached(f"history:{symbol}:{days}", TTL_HISTORY, lambda: _fetch_history(symbol, days)) or []


def get_news(symbol: str, limit: int = 6) -> list[dict]:
    """Recent headlines as ``[{title, publisher, link, summary, published}]``.

    Returns an empty list when the provider has nothing. The previous version
    fabricated a summary from empty fields and shipped ``"reported by , "`` with
    a 1970 date to the dashboard.
    """
    symbol = symbol.upper()

    if _simulated_quote(symbol) is not None:
        return []

    return _cached(f"news:{symbol}:{limit}", TTL_NEWS, lambda: _fetch_news(symbol, limit)) or []


def warm(symbols=TRACKED_SYMBOLS) -> int:
    """Pre-populate the cache. Called by the ``warm_market_cache`` command."""
    warmed = 0
    for symbol in symbols:
        if get_quote(symbol).price > 0:
            warmed += 1
    return warmed


# --------------------------------------------------------------------------- #
# Provider adapters                                                            #
# --------------------------------------------------------------------------- #
# Kept separate from the cache layer so a provider change touches only this
# section, and so the shape returned to callers is stable.

def _fetch_quote(symbol: str) -> dict | None:
    ticker = yf.Ticker(provider_symbol(symbol))

    # fast_info is a single lightweight request; .info is a much heavier one, so
    # try the cheap path first and only fall back when it comes up empty.
    price = change = None
    try:
        fast = ticker.fast_info
        price = fast.get("last_price")
        previous = fast.get("previous_close")
        if price and previous:
            change = (price - previous) / previous * 100
    except Exception:
        logger.debug("fast_info unavailable for %s", symbol, exc_info=True)

    info = _fetch_profile(symbol) or {}

    if not price:
        price = info.get("regularMarketPrice") or info.get("currentPrice")
    if not price:
        return None

    if change is None:
        previous = info.get("regularMarketPreviousClose")
        change = (price - previous) / previous * 100 if previous else 0.0

    return Quote(
        symbol=symbol,
        name=info.get("longName") or info.get("shortName") or symbol,
        price=round(float(price), 2),
        change_percent=round(float(change), 2),
        currency=currency_for(symbol),
        sector=info.get("sector") or "Unknown",
        market_cap=info.get("marketCap"),
    ).as_dict()


def _fetch_profile(symbol: str) -> dict | None:
    """Company metadata. Cached for half a day -- a sector does not change."""

    def load():
        info = yf.Ticker(provider_symbol(symbol)).info
        # Keep only what is rendered. The raw payload is ~150 keys.
        return {
            k: info.get(k)
            for k in (
                "longName",
                "shortName",
                "sector",
                "industry",
                "marketCap",
                "trailingPE",
                "regularMarketPrice",
                "currentPrice",
                "regularMarketPreviousClose",
            )
        }

    return _cached(f"profile:{symbol}", TTL_PROFILE, load)


def _fetch_history(symbol: str, days: int) -> list[dict]:
    """Daily closes from the provider, with the gaps dropped rather than carried.

    The provider returns a row for days it has no price for, with ``NaN`` in the
    close. ``float(NaN)`` and ``round(NaN, 2)`` are both NaN and neither raises,
    so those rows used to travel all the way out of here and break two things
    well away from the cause:

    * ``json.dumps`` refuses NaN, so the Oracle's chart question returned a 500
      whenever a drawn symbol had a gap — intermittent, because which symbols
      are drawn depends on the day.
    * The Rank It board computed a NaN change, failed SQLite's ``JSON_VALID``
      constraint, and was quietly skipped every day it included such a symbol.

    A day with no price is not a data point, so it does not become one.
    """
    frame = yf.Ticker(provider_symbol(symbol)).history(period=f"{days}d", interval="1d")
    if frame.empty:
        return []

    points = []
    for index, row in frame.iterrows():
        close = float(row["Close"])
        if not math.isfinite(close):
            continue

        volume = row.get("Volume")
        volume = int(volume) if volume is not None and math.isfinite(float(volume)) else 0

        points.append({
            "date": index.date().isoformat(),
            "close": round(close, 2),
            "volume": volume,
        })

    return points


def get_market_news(limit: int = 8) -> list[dict]:
    """The day's headlines across the tracked universe, most recent first.

    A single symbol's feed goes quiet for days at a time, so the wire used to
    show the same four stories all week. This pulls from several listings at
    once, rotates which ones lead on a daily cycle so the mix genuinely turns
    over, then dedupes and sorts by publication time.

    Cached for fifteen minutes: fresh enough to be a news feed, long enough that
    a page load never waits on eight provider calls.
    """
    return _cached(f"news:market:{limit}:{date.today()}", TTL_NEWS, lambda: _fetch_market_news(limit)) or []


# How many listings to poll for one wire. More would be slower without being
# meaningfully more varied — the same wire services syndicate across all of them.
NEWS_SOURCES = 5


def _fetch_market_news(limit: int) -> list[dict]:
    """Merge several symbols' feeds into one wire."""
    universe = list(TRACKED_SYMBOLS)
    start = date.today().toordinal() * NEWS_SOURCES
    leaders = [universe[(start + offset) % len(universe)] for offset in range(NEWS_SOURCES)]

    seen: set[str] = set()
    articles = []

    for symbol in leaders:
        try:
            for article in _fetch_news(symbol, limit):
                key = (article.get("link") or article["title"]).strip().lower()
                if key in seen:
                    continue
                seen.add(key)
                articles.append({**article, "symbol": symbol})
        except Exception:
            logger.warning("news unavailable for %s", symbol, exc_info=True)

    articles.sort(key=lambda article: _published_at(article), reverse=True)
    return articles[:limit]


def _published_at(article: dict) -> float:
    """Sort key. Handles the epoch seconds and the ISO string the provider mixes."""
    raw = article.get("published")
    if isinstance(raw, (int, float)):
        return float(raw)
    if isinstance(raw, str) and raw:
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return 0.0
    return 0.0


def _fetch_news(symbol: str, limit: int) -> list[dict]:
    """Normalise the provider's news payload.

    yfinance moved every field under a ``content`` object. Reading the old flat
    keys is why the dashboard rendered an empty headline dated 1 January 1970.
    Both shapes are handled so a provider rollback does not break the feed again.
    """
    articles = []

    for item in yf.Ticker(provider_symbol(symbol)).news or []:
        body = item.get("content") or item
        title = (body.get("title") or "").strip()
        if not title:
            continue

        provider = body.get("provider") or {}
        url = body.get("canonicalUrl") or body.get("clickThroughUrl") or {}

        articles.append(
            {
                "title": title,
                "publisher": provider.get("displayName") or body.get("publisher") or "",
                "link": url.get("url") if isinstance(url, dict) else (body.get("link") or ""),
                "summary": (body.get("summary") or body.get("description") or "").split("\n")[0],
                "published": body.get("pubDate") or body.get("providerPublishTime") or "",
            }
        )
        if len(articles) >= limit:
            break

    return articles


def _simulated_history(symbol: str, days: int) -> list[dict]:
    """Deterministic price walk for a fictional stock.

    Seeded from the symbol so the chart is stable across requests, and drifted
    by the stock's configured trend so the line matches its quoted change.
    """
    import random

    from users.models import CustomStock

    stock = CustomStock.objects.filter(symbol=symbol.upper()).first()
    if stock is None:
        return []

    rng = random.Random(f"{symbol}:{days}")
    drift = {"bullish": 0.0022, "bearish": -0.0022}.get(stock.trend or "", 0.0)
    volatility = float(stock.trend_strength or 0.5) * 0.02 + 0.006

    price = float(stock.current_price)
    closes = []
    # Walk backwards from today's price, then reverse, so the series always ends
    # on the quoted price rather than drifting away from it.
    for _ in range(days):
        closes.append(round(price, 2))
        price /= 1 + drift + rng.gauss(0, volatility)

    today = date.today()
    return [
        {
            "date": (today - timedelta(days=offset)).isoformat(),
            "close": close,
            "volume": rng.randint(400_000, 4_000_000),
        }
        for offset, close in enumerate(closes)
    ][::-1]
