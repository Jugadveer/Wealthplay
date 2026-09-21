"""
Ledger and Rank It.

Both follow the same contract as :mod:`puzzles`: a builder returns
``(payload, solution)``, the payload holds only what the client may see, and the
round is picked with ``daily_pick`` so nothing repeats until the whole list has
been used.
"""

from __future__ import annotations

import logging
import math
from datetime import date

from market_data import services

from .models import PuzzleKind
from .puzzles import PUZZLE_UNIVERSE, daily_pick
from .words import LEDGER_WORDS

logger = logging.getLogger(__name__)

LEDGER_MAX_GUESSES = 6
RANK_SIZE = 4


# --------------------------------------------------------------------------- #
# Ledger — the word game                                                       #
# --------------------------------------------------------------------------- #

def build_ledger(day: date) -> tuple[dict, dict]:
    """A five-letter financial term in six tries."""
    word, meaning = daily_pick(list(LEDGER_WORDS), day, PuzzleKind.LEDGER)[0]
    return (
        {'length': len(word), 'max_guesses': LEDGER_MAX_GUESSES},
        {'word': word, 'meaning': meaning},
    )


def mark_guess(guess: str, answer: str) -> list[str]:
    """Per-letter feedback: ``hit``, ``near`` or ``miss``.

    Two passes, because one pass gets duplicate letters wrong. Guessing SPLIT
    against STOCK must mark only the first S, not both, so exact matches are
    claimed first and the leftovers are what a near match may draw from.
    """
    marks = ['miss'] * len(guess)
    remaining: dict[str, int] = {}

    for index, letter in enumerate(answer):
        if guess[index] == letter:
            marks[index] = 'hit'
        else:
            remaining[letter] = remaining.get(letter, 0) + 1

    for index, letter in enumerate(guess):
        if marks[index] == 'hit':
            continue
        if remaining.get(letter):
            marks[index] = 'near'
            remaining[letter] -= 1

    return marks


def score_ledger(guess_count: int, solved: bool) -> int:
    """Fewer guesses, more points. An unsolved board still scores nothing."""
    if not solved:
        return 0
    return max(10, 60 - (guess_count - 1) * 10)


def ledger_share(marks: list[list[str]], day: date, solved: bool) -> str:
    """The emoji grid — what makes a result worth posting."""
    glyphs = {'hit': '🟩', 'near': '🟨', 'miss': '⬛'}
    rows = '\n'.join(''.join(glyphs[mark] for mark in row) for row in marks)
    used = len(marks) if solved else 'X'
    return f'Ledger {day.day} {day:%b} — {used}/{LEDGER_MAX_GUESSES}\n{rows}'


# --------------------------------------------------------------------------- #
# Rank It — order four listings by last year's return                          #
# --------------------------------------------------------------------------- #

def build_rank(day: date) -> tuple[dict, dict]:
    """Put four companies in order, best return first.

    Returns are computed from real history. Any symbol without enough history is
    dropped rather than ranked on a guess, so the answer is always checkable.
    """
    picks = daily_pick(PUZZLE_UNIVERSE, day, PuzzleKind.RANK, count=RANK_SIZE * 2)

    measured = []
    for symbol, name, sector in picks:
        change = _year_change(symbol)
        if change is not None:
            measured.append({'symbol': symbol, 'name': name, 'sector': sector, 'change': change})
        if len(measured) == RANK_SIZE:
            break

    if len(measured) < 2:
        raise RuntimeError('not enough price history to build a Rank It board')

    ranked = sorted(measured, key=lambda item: item['change'], reverse=True)

    # The board is shown in the order the cycle produced, which is unrelated to
    # the answer; sorting it here would hand the player the solution.
    return (
        {
            'cards': [
                {'symbol': item['symbol'], 'name': item['name'], 'sector': item['sector']}
                for item in measured
            ],
            'window': 'past year',
        },
        {
            'order': [item['symbol'] for item in ranked],
            'changes': {item['symbol']: round(item['change'], 1) for item in ranked},
        },
    )


def _year_change(symbol: str) -> float | None:
    """A symbol's change over the window, or ``None`` if it cannot be measured.

    Every close is checked for being a finite number, not merely present. One
    NaN in a series propagates through the subtraction, and NaN is truthy, so
    the old `not closes[0]` guard let it past. Two things then broke, both
    silently:

    * ``json.dumps`` writes bare ``NaN``, which Python accepts and JSON does
      not, so SQLite rejected the row on its ``JSON_VALID`` constraint and the
      Rank It board failed to save every single day.
    * ``sorted`` against NaN returns an arbitrary order, so the answer would
      have been wrong even if it had saved.
    """
    series = services.get_history(symbol, days=250)
    closes = [
        point['close']
        for point in series
        if isinstance(point.get('close'), (int, float)) and math.isfinite(point['close'])
    ]

    if len(closes) < 100 or not closes[0]:
        return None

    change = (closes[-1] - closes[0]) / closes[0] * 100
    return change if math.isfinite(change) else None


def score_rank(submitted: list[str], answer: list[str]) -> tuple[int, int, int]:
    """Return ``(points, concordant_pairs, total_pairs)``.

    Scored on pairs rather than exact positions: someone who knows the winner
    and the loser but flips the middle two has understood most of the board, and
    an all-or-nothing score would tell them nothing.
    """
    position = {symbol: index for index, symbol in enumerate(submitted)}
    pairs = concordant = 0

    for better in range(len(answer)):
        for worse in range(better + 1, len(answer)):
            pairs += 1
            if position.get(answer[better], 99) < position.get(answer[worse], 99):
                concordant += 1

    points = round(50 * concordant / pairs) if pairs else 0
    return points, concordant, pairs
