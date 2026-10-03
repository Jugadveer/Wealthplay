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
from datetime import date, datetime, timedelta, timezone

from curl_cffi import requests as curl_requests
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


def get_history_between(symbol: str, start: date, end: date) -> list[dict]:
    """Daily closes across an explicit window, oldest first.

    Used by the hindsight replay, which holds today's positions through a past
    crash. Simulated symbols return nothing rather than a generated series: they
    have no history to replay, and inventing one would be the opposite of the
    point.
    """
    symbol = symbol.upper()
    if _simulated_quote(symbol) is not None:
        return []

    key = f"history:{symbol}:{start.isoformat()}:{end.isoformat()}"
    return _cached(key, TTL_HISTORY, lambda: _fetch_history_between(symbol, start, end)) or []


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
#
# These used to go through `yfinance`, which returns pandas DataFrames and
# therefore drags pandas and numpy in behind it. That is 119 MB of wheels to
# read a few hundred numbers out of a JSON response, and it put the deployed
# function over a serverless size limit — 242 MB against a 225 MB cap.
#
# So the JSON endpoints are called directly. `curl_cffi` stays, because it is
# the part of yfinance that actually mattered: Yahoo rejects a plain `requests`
# client on TLS fingerprint, and `impersonate` is what gets past that.
#
# Nothing else changed. The same fields come back, including sector and market
# cap, and gap days still arrive as nulls rather than NaN.

CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
SEARCH_URL = "https://query1.finance.yahoo.com/v1/finance/search"
SUMMARY_URL = "https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
CRUMB_URL = "https://query1.finance.yahoo.com/v1/test/getcrumb"
COOKIE_URL = "https://fc.yahoo.com"

PROVIDER_TIMEOUT = 20
IMPERSONATE = "chrome"

_session_state: dict = {}


def _session():
    """A browser-shaped session, with the crumb the private endpoints want.

    The chart and search endpoints are open. `quoteSummary` — the only source of
    sector and market cap without an API key — answers 401 "Invalid Crumb"
    unless a cookie is presented along with a token fetched using it.

    Held per process and rebuilt on rejection, because the crumb expires and a
    stale one looks exactly like a missing one.
    """
    if "session" not in _session_state:
        session = curl_requests.Session(impersonate=IMPERSONATE)
        crumb = ""
        try:
            session.get(COOKIE_URL, timeout=PROVIDER_TIMEOUT)
            response = session.get(CRUMB_URL, timeout=PROVIDER_TIMEOUT)
            candidate = (response.text or "").strip()
            # An error page is HTML, and an HTML crumb fails every later call.
            if response.status_code == 200 and candidate and "<" not in candidate:
                crumb = candidate
        except Exception:
            logger.debug("could not establish a provider session", exc_info=True)
        _session_state["session"] = session
        _session_state["crumb"] = crumb

    return _session_state["session"], _session_state["crumb"]


def _reset_session() -> None:
    _session_state.clear()


def _json(url: str, params: dict | None = None, *, with_crumb: bool = False) -> dict | None:
    """One GET, returning parsed JSON or ``None``.

    Never raises. A provider failure has to degrade to stale cache rather than a
    500, and :func:`_cached` is what decides that.
    """
    for attempt in range(2):
        session, crumb = _session()
        query = dict(params or {})
        if with_crumb:
            if not crumb:
                return None
            query["crumb"] = crumb

        try:
            response = session.get(url, params=query, timeout=PROVIDER_TIMEOUT)
        except Exception:
            logger.warning("provider request failed: %s", url, exc_info=True)
            return None

        if response.status_code == 401 and attempt == 0:
            # The crumb went stale. Rebuild it once and try again.
            _reset_session()
            continue
        if response.status_code != 200:
            logger.warning("provider %s -> %s", url, response.status_code)
            return None

        try:
            return response.json()
        except Exception:
            logger.warning("provider returned unparsable JSON: %s", url, exc_info=True)
            return None

    return None


def _chart(symbol: str, **params) -> dict | None:
    """The chart payload for a symbol: metadata, timestamps and daily bars."""
    payload = _json(CHART_URL.format(symbol=provider_symbol(symbol)),
                    {"interval": "1d", **params})
    try:
        results = payload["chart"]["result"]
    except (TypeError, KeyError):
        return None
    return results[0] if results else None


def _bars(chart: dict) -> list[dict]:
    """Daily closes from a chart payload, with the gaps dropped rather than carried.

    The provider returns an entry for days it has no price for, with ``null`` in
    the close. Those used to arrive from pandas as ``NaN``, which neither
    ``float()`` nor ``round()`` complains about, so they travelled out of here
    intact and broke two things far from the cause:

    * ``json.dumps`` refuses NaN, so the Oracle's chart question returned a 500
      whenever a drawn symbol had a gap — intermittent, because which symbols
      are drawn depends on the day.
    * The Rank It board computed a NaN change, failed SQLite's ``JSON_VALID``
      constraint, and was quietly skipped every day it included such a symbol.

    A day with no price is not a data point, so it does not become one.
    """
    timestamps = chart.get("timestamp") or []
    quote = (chart.get("indicators", {}).get("quote") or [{}])[0]
    closes = quote.get("close") or []
    volumes = quote.get("volume") or []

    points = []
    for index, stamp in enumerate(timestamps):
        close = closes[index] if index < len(closes) else None
        if close is None or not math.isfinite(close):
            continue

        volume = volumes[index] if index < len(volumes) else None
        points.append({
            "date": datetime.fromtimestamp(stamp, tz=timezone.utc).date().isoformat(),
            "close": round(float(close), 2),
            "volume": int(volume) if volume else 0,
        })

    return points


def _fetch_quote(symbol: str) -> dict | None:
    """Current price and the day's move.

    The change is computed from the last two closes rather than read from the
    metadata: `chartPreviousClose` is the close before the requested window, so
    on a year-long range it reports the move since last year.
    """
    chart = _chart(symbol, range="5d")
    if chart is None:
        return None

    meta = chart.get("meta") or {}
    price = meta.get("regularMarketPrice")
    bars = _bars(chart)

    if price is None and bars:
        price = bars[-1]["close"]
    if price is None:
        return None

    previous = meta.get("previousClose")
    if previous is None and len(bars) >= 2:
        previous = bars[-2]["close"]
    change = ((float(price) - previous) / previous * 100) if previous else 0.0

    info = _fetch_profile(symbol) or {}

    return Quote(
        symbol=symbol,
        name=info.get("name") or meta.get("longName") or meta.get("shortName") or symbol,
        price=round(float(price), 2),
        change_percent=round(float(change), 2),
        currency=currency_for(symbol),
        sector=info.get("sector") or "Unknown",
        market_cap=info.get("marketCap"),
    ).as_dict()


def _fetch_profile(symbol: str) -> dict | None:
    """Company metadata. Cached for half a day -- a sector does not change.

    Two sources, because they fail differently. `quoteSummary` carries both the
    sector and the market cap but needs a crumb; the search endpoint is open and
    carries the sector alone. Falling back keeps the ESG and concentration
    figures working on a day when the crumb cannot be had.
    """

    def load():
        ticker = provider_symbol(symbol)
        payload = _json(SUMMARY_URL.format(symbol=ticker),
                        {"modules": "assetProfile,price"}, with_crumb=True)
        try:
            result = payload["quoteSummary"]["result"][0]
        except (TypeError, KeyError, IndexError):
            result = None

        if result:
            profile = result.get("assetProfile") or {}
            price = result.get("price") or {}
            return {
                "name": (price.get("longName") or price.get("shortName") or ""),
                "sector": profile.get("sector") or "",
                "industry": profile.get("industry") or "",
                "marketCap": (price.get("marketCap") or {}).get("raw"),
            }

        search = _json(SEARCH_URL, {"q": ticker, "quotesCount": 4, "newsCount": 0}) or {}
        for quote in search.get("quotes") or []:
            if quote.get("symbol") == ticker:
                return {
                    "name": quote.get("longname") or quote.get("shortname") or "",
                    "sector": quote.get("sector") or "",
                    "industry": quote.get("industry") or "",
                    "marketCap": None,
                }
        return {}

    return _cached(f"profile:{symbol}", TTL_PROFILE, load)


def _fetch_history(symbol: str, days: int) -> list[dict]:
    """Daily closes for the last ``days`` days."""
    end = date.today()
    chart = _chart(symbol, **_window(end - timedelta(days=days), end))
    return _bars(chart) if chart else []


def _fetch_history_between(symbol: str, start: date, end: date) -> list[dict]:
    """Daily closes across an explicit window, for the hindsight replay."""
    chart = _chart(symbol, **_window(start, end))
    return _bars(chart) if chart else []


def _window(start: date, end: date) -> dict:
    """A date range as the provider's inclusive Unix-timestamp parameters."""
    midnight = datetime.min.time()
    return {
        "period1": int(datetime.combine(start, midnight, tzinfo=timezone.utc).timestamp()),
        "period2": int(datetime.combine(end + timedelta(days=1), midnight,
                                        tzinfo=timezone.utc).timestamp()),
    }


def _fetch_news(symbol: str, limit: int) -> list[dict]:
    """Headlines for a symbol.

    The previous version read a yfinance payload whose fields had moved under a
    `content` object, which is why the dashboard once rendered an empty headline
    dated 1 January 1970. A story with no title is dropped rather than shown.
    """
    payload = _json(SEARCH_URL, {
        "q": provider_symbol(symbol),
        "newsCount": max(limit, 1),
        "quotesCount": 0,
    }) or {}

    articles = []
    for item in payload.get("news") or []:
        title = (item.get("title") or "").strip()
        if not title:
            continue

        published = item.get("providerPublishTime")
        articles.append({
            "title": title,
            "publisher": item.get("publisher") or "",
            "link": item.get("link") or "",
            "summary": (item.get("summary") or "").split("\n")[0],
            "published": (
                datetime.fromtimestamp(published, tz=timezone.utc).isoformat()
                if isinstance(published, (int, float)) and published else ""
            ),
        })
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
