"""
Puzzle generation.

Every generator is seeded from the date, so all players get the same puzzle and
a shared score means something. The seed is the only source of randomness —
regenerating a past day reproduces it exactly.
"""

from __future__ import annotations

import hashlib
import logging
import random
from datetime import date

from market_data import services
from users.portfolio import pricing

from .facts import ESTIMATE_FACTS
from .models import DailyPuzzle, PuzzleKind

logger = logging.getLogger(__name__)

TICKER_MAX_GUESSES = 5

# The universe for Ticker Tiles. Large, recognisable listings across both
# markets, so the puzzle is winnable by someone who reads the news.
PUZZLE_UNIVERSE = [
    ('AAPL', 'Apple', 'Technology'),
    ('MSFT', 'Microsoft', 'Technology'),
    ('GOOGL', 'Alphabet', 'Communication Services'),
    ('AMZN', 'Amazon', 'Consumer Cyclical'),
    ('NVDA', 'NVIDIA', 'Technology'),
    ('META', 'Meta Platforms', 'Communication Services'),
    ('TSLA', 'Tesla', 'Consumer Cyclical'),
    ('RELIANCE', 'Reliance Industries', 'Energy'),
    ('TCS', 'Tata Consultancy Services', 'Technology'),
    ('INFY', 'Infosys', 'Technology'),
    ('HDFCBANK', 'HDFC Bank', 'Financial Services'),
    ('ICICIBANK', 'ICICI Bank', 'Financial Services'),
    ('SBIN', 'State Bank of India', 'Financial Services'),
    ('ITC', 'ITC', 'Consumer Defensive'),
    ('BHARTIARTL', 'Bharti Airtel', 'Communication Services'),
]


def daily_pick(items: list, day: date, kind: str, count: int = 1) -> list:
    """Pick from ``items`` so that nothing repeats until everything has been used.

    ``rng.choice`` was drawing independently each day, so the same ticker could
    come up twice in a week and Number Sense repeated a question inside a
    fortnight. Instead the list is shuffled once with a fixed seed and then
    walked in order, which makes the cycle exactly as long as the list, is
    identical for every player, and still looks unordered.
    """
    order = list(items)
    random.Random(f'wealthplay:cycle:{kind}').shuffle(order)

    start = day.toordinal() * count
    return [order[(start + offset) % len(order)] for offset in range(count)]


def seeded_random(day: date, kind: str) -> random.Random:
    """A generator that depends only on the day and puzzle kind."""
    digest = hashlib.sha256(f'wealthplay:{day.isoformat()}:{kind}'.encode()).hexdigest()
    return random.Random(int(digest[:16], 16))


def get_or_create(day: date, kind: str) -> DailyPuzzle:
    """Today's puzzle, building it on first request."""
    existing = DailyPuzzle.objects.filter(puzzle_date=day, kind=kind).first()
    if existing:
        return existing

    # Imported here rather than at module scope: games.py needs PUZZLE_UNIVERSE
    # and daily_pick from this module, so a top-level import would be circular.
    from . import games

    builders = {
        PuzzleKind.TICKER: _build_ticker,
        PuzzleKind.CALL: _build_call,
        PuzzleKind.ESTIMATE: _build_estimate,
        PuzzleKind.LEDGER: games.build_ledger,
        PuzzleKind.RANK: games.build_rank,
    }
    payload, solution = builders[kind](day)

    puzzle, _ = DailyPuzzle.objects.get_or_create(
        puzzle_date=day,
        kind=kind,
        defaults={'payload': payload, 'solution': solution},
    )
    return puzzle


# --------------------------------------------------------------------------- #
# Ticker Tiles                                                                 #
# --------------------------------------------------------------------------- #

def _build_ticker(day: date) -> tuple[dict, dict]:
    """Guess the company in five tries, one clue revealed per wrong guess.

    Clues run from broad to narrow, so an informed player can often get it in
    two or three and a beginner still converges by five.
    """
    symbol, name, sector = daily_pick(PUZZLE_UNIVERSE, day, PuzzleKind.TICKER)[0]

    quote = pricing.quote(symbol)
    series = services.get_history(symbol, days=250)
    closes = [point['close'] for point in series]

    year_move = ((closes[-1] - closes[0]) / closes[0] * 100) if len(closes) > 100 else None

    clues = [
        {'label': 'Sector', 'value': sector},
        {'label': 'Listed in', 'value': 'India' if quote['currency'] == 'INR' else 'United States'},
        {'label': 'Market cap', 'value': _cap_band(quote.get('market_cap'), quote['currency'])},
        {
            'label': 'Past year',
            'value': f'{year_move:+.0f}%' if year_move is not None else 'Not enough history',
        },
        {'label': 'Starts with', 'value': name[0].upper()},
    ]

    return (
        {
            'max_guesses': TICKER_MAX_GUESSES,
            'clues': clues,
            # A normalised silhouette: the shape is the clue, the level is not.
            'silhouette': _silhouette(closes),
        },
        {'symbol': symbol, 'name': name},
    )


def _cap_band(market_cap, currency: str) -> str:
    """A band rather than an exact figure — the number would give it away."""
    if not market_cap:
        return 'Not disclosed'

    unit = '₹' if currency == 'INR' else '$'
    value = market_cap * 85 if currency == 'INR' else market_cap

    for threshold, label in (
        (2e12, f'over {unit}2 trillion'),
        (5e11, f'{unit}500 billion to {unit}2 trillion'),
        (1e11, f'{unit}100 to {unit}500 billion'),
        (0, f'under {unit}100 billion'),
    ):
        if value >= threshold:
            return label
    return 'Not disclosed'


def _silhouette(closes: list[float], points: int = 40) -> list[float]:
    """Downsample and scale a series to 0-1 so only its shape survives."""
    if len(closes) < points:
        return []

    step = len(closes) / points
    sampled = [closes[int(i * step)] for i in range(points)]
    low, high = min(sampled), max(sampled)
    span = high - low

    return [round((value - low) / span, 3) if span else 0.5 for value in sampled]


def search_universe(query: str) -> list[dict]:
    """Autocomplete for the guess box, restricted to the puzzle universe.

    Guessing is multiple-choice-with-search rather than free text: the game is
    about reading clues, not about spelling.
    """
    query = query.strip().lower()
    if not query:
        return []

    return [
        {'symbol': symbol, 'name': name}
        for symbol, name, _ in PUZZLE_UNIVERSE
        if query in name.lower() or query in symbol.lower()
    ][:8]


def score_ticker(guess_count: int, solved: bool) -> int:
    """Fewer guesses, more points. An unsolved board still scores nothing."""
    return max(0, 60 - (guess_count - 1) * 10) if solved else 0


# --------------------------------------------------------------------------- #
# Market Call                                                                  #
# --------------------------------------------------------------------------- #

def _build_call(day: date) -> tuple[dict, dict]:
    """A binary call on one index or large-cap, resolved from the next close."""
    symbol, name, _ = daily_pick(PUZZLE_UNIVERSE, day, PuzzleKind.CALL)[0]

    quote = pricing.quote(symbol)
    series = services.get_history(symbol, days=30)

    return (
        {
            'symbol': symbol,
            'name': name,
            'currency': quote['currency'],
            'reference_price': quote['price'],
            'series': [{'date': p['date'], 'close': p['close']} for p in series[-20:]],
            'question': (
                f'Does {name} close higher or lower than '
                f'{"₹" if quote["currency"] == "INR" else "$"}{quote["price"]:,.2f} tomorrow?'
            ),
        },
        {'reference_price': quote['price'], 'resolved': False, 'outcome': None},
    )


def resolve_call(puzzle: DailyPuzzle) -> dict:
    """Settle a past call against the current price.

    Returns the solution unchanged if the market has not moved on yet.
    """
    if puzzle.solution.get('resolved'):
        return puzzle.solution

    symbol = puzzle.payload['symbol']
    reference = puzzle.solution['reference_price']
    current = pricing.quote(symbol)['price']

    if current <= 0 or puzzle.puzzle_date >= date.today():
        return puzzle.solution

    move = (current - reference) / reference * 100
    puzzle.solution = {
        'reference_price': reference,
        'settle_price': current,
        'move_percent': round(move, 2),
        'outcome': 'higher' if move > 0 else 'lower',
        'resolved': True,
    }
    puzzle.save(update_fields=['solution'])
    return puzzle.solution


# --------------------------------------------------------------------------- #
# Number Sense                                                                 #
# --------------------------------------------------------------------------- #

def _build_estimate(day: date) -> tuple[dict, dict]:
    """Guess a real figure. Scored on how close, not on being exact."""
    fact = daily_pick(ESTIMATE_FACTS, day, PuzzleKind.ESTIMATE)[0]

    return (
        {'question': fact['question'], 'unit': fact['unit']},
        {'answer': fact['answer'], 'context': fact['context']},
    )


def score_estimate(guess: float, answer: float) -> tuple[int, str]:
    """Return ``(points, band)`` from the relative error.

    Proximity banding is the point: knowing gold is "about a lakh" is useful,
    and demanding the exact rupee would teach nothing.
    """
    if answer == 0:
        return (0, 'way off')

    error = abs(guess - answer) / abs(answer) * 100

    for limit, points, band in (
        (2, 50, 'spot on'),
        (10, 35, 'very close'),
        (25, 20, 'close'),
        (50, 10, 'in the region'),
    ):
        if error <= limit:
            return (points, band)
    return (0, 'way off')
