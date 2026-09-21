"""Daily edition endpoints."""

from __future__ import annotations

import logging

from datetime import date, timedelta

from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ai import tutor
from users.models import UserProfile

from . import games, puzzles, review
from .models import DailyPuzzle, PuzzleAttempt, PuzzleKind, ReviewCard, Streak

logger = logging.getLogger(__name__)


def _streak_for(user) -> Streak:
    streak, _ = Streak.objects.get_or_create(user=user)
    return streak


def _attempt_for(user, puzzle: DailyPuzzle) -> PuzzleAttempt:
    attempt, _ = PuzzleAttempt.objects.get_or_create(user=user, puzzle=puzzle)
    return attempt


def _complete(attempt: PuzzleAttempt, *, solved: bool, score: int) -> None:
    """Close out an attempt and credit the score once."""
    attempt.solved = solved
    attempt.finished = True
    attempt.score = score
    attempt.finished_at = timezone.now()
    attempt.save()

    if score:
        UserProfile.objects.filter(user=attempt.user).update(xp=_current_xp(attempt.user) + score)
    _streak_for(attempt.user).register()


def _current_xp(user) -> int:
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile.xp


PLAYABLE_KINDS = (
    PuzzleKind.TICKER,
    PuzzleKind.LEDGER,
    PuzzleKind.CALL,
    PuzzleKind.RANK,
    PuzzleKind.ESTIMATE,
)


def _safe_puzzle(day: date, kind: str) -> DailyPuzzle | None:
    """Build a puzzle, or report none.

    Rank It needs a year of prices for several symbols. If the provider cannot
    supply them, that one game is missing from today's set — which is better
    than the whole page failing on it.
    """
    try:
        return puzzles.get_or_create(day, kind)
    except Exception:
        logger.warning('could not build the %s puzzle for %s', kind, day, exc_info=True)
        return None


# --------------------------------------------------------------------------- #
# Today                                                                        #
# --------------------------------------------------------------------------- #

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def today(request):
    """Everything in today's edition, in one request."""
    day = date.today()
    streak = _streak_for(request.user)

    plays = []
    for kind in PLAYABLE_KINDS:
        puzzle = _safe_puzzle(day, kind)
        if puzzle is None:
            continue
        attempt = PuzzleAttempt.objects.filter(user=request.user, puzzle=puzzle).first()
        plays.append(
            {
                'kind': kind,
                'label': PuzzleKind(kind).label,
                'done': bool(attempt and attempt.finished),
                'solved': bool(attempt and attempt.solved),
                'score': attempt.score if attempt else 0,
                # A market call is placed today and settles tomorrow, so it is
                # neither untouched nor finished in between. Every other game
                # resolves immediately, so a part-played board is in progress,
                # not pending — labelling Ledger "settles tomorrow" was wrong.
                'pending': bool(
                    kind == PuzzleKind.CALL and attempt and attempt.guesses and not attempt.finished
                ),
                'in_progress': bool(
                    kind != PuzzleKind.CALL and attempt and attempt.guesses and not attempt.finished
                ),
            }
        )

    due_count = ReviewCard.objects.filter(user=request.user, due_on__lte=day).count()
    plays.append(
        {
            'kind': 'drill',
            'label': 'Daily Drill',
            'done': due_count == 0 and ReviewCard.objects.filter(user=request.user).exists(),
            'solved': False,
            'score': 0,
            'due_count': due_count,
        }
    )

    return Response(
        {
            'date': day.isoformat(),
            'plays': plays,
            'streak': streak.status(day),
            'completed_today': sum(1 for play in plays if play['done']),
        }
    )


# --------------------------------------------------------------------------- #
# Ticker Tiles                                                                 #
# --------------------------------------------------------------------------- #

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ticker_board(request):
    """The board, showing only the clues this player has unlocked."""
    puzzle = puzzles.get_or_create(date.today(), PuzzleKind.TICKER)
    attempt = _attempt_for(request.user, puzzle)
    revealed = len(attempt.guesses)

    return Response(
        {
            'max_guesses': puzzle.payload['max_guesses'],
            'guesses': attempt.guesses,
            'clues': puzzle.payload['clues'][:revealed],
            'silhouette': puzzle.payload['silhouette'] if revealed >= 2 else [],
            'finished': attempt.finished,
            'solved': attempt.solved,
            'score': attempt.score,
            # Revealed only once the board is closed, win or lose.
            'answer': puzzle.solution if attempt.finished else None,
            'share': _share_grid(attempt, puzzle) if attempt.finished else None,
        }
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ticker_search(request):
    """Autocomplete for the guess box."""
    return Response({'results': puzzles.search_universe(request.query_params.get('q', ''))})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ticker_guess(request):
    """Submit one guess."""
    puzzle = puzzles.get_or_create(date.today(), PuzzleKind.TICKER)
    attempt = _attempt_for(request.user, puzzle)

    if attempt.finished:
        return Response({'error': "Today's board is already closed."}, status=400)

    guess = (request.data.get('symbol') or '').strip().upper()
    if not guess:
        return Response({'error': 'Pick a company.'}, status=400)
    if any(g['symbol'] == guess for g in attempt.guesses):
        return Response({'error': 'You already tried that one.'}, status=400)

    correct = guess == puzzle.solution['symbol']
    attempt.guesses.append({'symbol': guess, 'correct': correct})
    used = len(attempt.guesses)
    out_of_guesses = used >= puzzle.payload['max_guesses']

    if correct or out_of_guesses:
        _complete(attempt, solved=correct, score=puzzles.score_ticker(used, correct))
    else:
        attempt.save()

    return Response(
        {
            'correct': correct,
            'guesses': attempt.guesses,
            'clues': puzzle.payload['clues'][:used],
            'silhouette': puzzle.payload['silhouette'] if used >= 2 else [],
            'finished': attempt.finished,
            'solved': attempt.solved,
            'score': attempt.score,
            'answer': puzzle.solution if attempt.finished else None,
            'share': _share_grid(attempt, puzzle) if attempt.finished else None,
        }
    )


def _share_grid(attempt: PuzzleAttempt, puzzle: DailyPuzzle) -> str:
    """The emoji grid — what makes a result worth posting."""
    squares = ''.join('🟩' if g['correct'] else '⬛' for g in attempt.guesses)
    used = len(attempt.guesses) if attempt.solved else 'X'
    # Built without platform-specific strftime directives: "%-d" is glibc-only
    # and raises ValueError on Windows.
    day = f'{puzzle.puzzle_date.day} {puzzle.puzzle_date:%b}'
    return f'Ticker Tiles {day} — {used}/{puzzle.payload["max_guesses"]}\n{squares}'


# --------------------------------------------------------------------------- #
# Market Call                                                                  #
# --------------------------------------------------------------------------- #

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def market_call(request):
    """Read today's call, or make one.

    A call placed today settles tomorrow, so the response reports the pending
    state rather than pretending to score it immediately.
    """
    puzzle = puzzles.get_or_create(date.today(), PuzzleKind.CALL)
    attempt = _attempt_for(request.user, puzzle)

    if request.method == 'POST':
        if attempt.guesses:
            return Response({'error': "You have already called today's market."}, status=400)

        call = (request.data.get('call') or '').lower()
        if call not in {'higher', 'lower'}:
            return Response({'error': 'Call it higher or lower.'}, status=400)

        attempt.guesses = [{'call': call, 'at': timezone.now().isoformat()}]
        attempt.save()
        _streak_for(request.user).register()

    yesterday = _settle_yesterday(request.user)

    return Response(
        {
            **puzzle.payload,
            'your_call': attempt.guesses[0]['call'] if attempt.guesses else None,
            'settles': (date.today() + timedelta(days=1)).isoformat(),
            'yesterday': yesterday,
        }
    )


def _settle_yesterday(user) -> dict | None:
    """Score the previous day's call, now that a close exists."""
    puzzle = DailyPuzzle.objects.filter(
        puzzle_date=date.today() - timedelta(days=1), kind=PuzzleKind.CALL
    ).first()
    if not puzzle:
        return None

    attempt = PuzzleAttempt.objects.filter(user=user, puzzle=puzzle).first()
    if not attempt or not attempt.guesses:
        return None

    solution = puzzles.resolve_call(puzzle)
    if not solution.get('resolved'):
        return None

    called = attempt.guesses[0]['call']
    correct = called == solution['outcome']

    if not attempt.finished:
        _complete(attempt, solved=correct, score=25 if correct else 0)

    return {
        'symbol': puzzle.payload['symbol'],
        'name': puzzle.payload['name'],
        'your_call': called,
        'outcome': solution['outcome'],
        'move_percent': solution['move_percent'],
        'correct': correct,
    }


# --------------------------------------------------------------------------- #
# Number Sense                                                                 #
# --------------------------------------------------------------------------- #

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def number_sense(request):
    """Read today's question, or answer it."""
    puzzle = puzzles.get_or_create(date.today(), PuzzleKind.ESTIMATE)
    attempt = _attempt_for(request.user, puzzle)

    if request.method == 'GET':
        return Response(
            {
                **puzzle.payload,
                'finished': attempt.finished,
                'result': attempt.guesses[-1] if attempt.finished else None,
            }
        )

    if attempt.finished:
        return Response({'error': "You have already answered today's question."}, status=400)

    try:
        guess = float(request.data.get('guess'))
    except (TypeError, ValueError):
        return Response({'error': 'Enter a number.'}, status=400)

    answer = puzzle.solution['answer']
    score, band = puzzles.score_estimate(guess, answer)

    result = {
        'guess': guess,
        'answer': answer,
        'band': band,
        'score': score,
        'off_by_percent': round(abs(guess - answer) / abs(answer) * 100, 1) if answer else None,
        'context': puzzle.solution['context'],
    }

    attempt.guesses.append(result)
    _complete(attempt, solved=score > 0, score=score)

    return Response({**puzzle.payload, 'finished': True, 'result': result})


# --------------------------------------------------------------------------- #
# Daily Drill                                                                  #
# --------------------------------------------------------------------------- #

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def drill(request):
    """Today's spaced-repetition set."""
    review.sync_cards(request.user)
    cards = review.todays_drill(request.user)

    if not cards:
        return Response(
            {
                'cards': [],
                'empty_reason': 'Finish a lesson module and its questions will start appearing here.',
            }
        )

    return Response({'cards': [review.serialise(card) for card in cards]})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def drill_answer(request):
    """Grade one drill answer and reschedule the card."""
    card = ReviewCard.objects.filter(id=request.data.get('card_id'), user=request.user).first()
    if not card:
        return Response({'error': 'That question is not in your queue.'}, status=404)

    try:
        chosen = int(request.data.get('choice'))
    except (TypeError, ValueError):
        return Response({'error': 'Choose an option.'}, status=400)

    result = review.answer(card, chosen)

    if result['correct']:
        UserProfile.objects.filter(user=request.user).update(xp=_current_xp(request.user) + 10)
    _streak_for(request.user).register()

    return Response(result)


# --------------------------------------------------------------------------- #
# Progress                                                                     #
# --------------------------------------------------------------------------- #

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def streak(request):
    """Streak state plus the last fortnight, for the calendar strip."""
    today_date = date.today()
    start = today_date - timedelta(days=13)

    active_days = set(
        PuzzleAttempt.objects.filter(
            user=request.user, finished_at__date__gte=start
        ).values_list('finished_at__date', flat=True)
    )

    return Response(
        {
            **_streak_for(request.user).status(today_date),
            'calendar': [
                {'date': (start + timedelta(days=offset)).isoformat(),
                 'active': (start + timedelta(days=offset)) in active_days}
                for offset in range(14)
            ],
        }
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recap(request):
    """The week in numbers, narrated."""
    since = date.today() - timedelta(days=7)

    attempts = PuzzleAttempt.objects.filter(user=request.user, finished_at__date__gte=since)
    solved = attempts.filter(solved=True).count()

    cards = ReviewCard.objects.filter(user=request.user)
    totals = cards.aggregate(reviews=Count('id'), lapses=Count('id', filter=Q(lapses__gt=0)))
    accuracy = (
        (totals['reviews'] - totals['lapses']) / totals['reviews'] * 100 if totals['reviews'] else 0
    )

    weakest = cards.order_by('-lapses').first()
    streak_state = _streak_for(request.user).status()

    from users.portfolio import value_portfolio
    from users.models import DemoPortfolio

    portfolio = DemoPortfolio.objects.filter(user=request.user).first()
    portfolio_return = value_portfolio(portfolio)['total_pnl_percent'] if portfolio else 0.0

    stats = {
        'puzzles': solved,
        'puzzle_days': 7,
        'accuracy': accuracy,
        'streak': streak_state['current'],
        'portfolio_return': portfolio_return,
        'weak_topic': weakest.module_id if weakest and weakest.lapses else 'nothing yet',
        'modules': 0,
    }

    narrative = tutor.weekly_recap(stats)

    return Response({'stats': stats, 'narrative': narrative, 'narrative_available': bool(narrative)})


# --------------------------------------------------------------------------- #
# Ledger                                                                       #
# --------------------------------------------------------------------------- #

def _ledger_state(attempt: PuzzleAttempt, puzzle: DailyPuzzle) -> dict:
    rows = attempt.guesses
    return {
        **puzzle.payload,
        'rows': rows,
        'finished': attempt.finished,
        'solved': attempt.solved,
        'score': attempt.score,
        # The word is only ever sent once the board is closed, win or lose.
        'answer': puzzle.solution if attempt.finished else None,
        'share': (
            games.ledger_share([row['marks'] for row in rows], puzzle.puzzle_date, attempt.solved)
            if attempt.finished
            else None
        ),
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ledger_board(request):
    """Today's word board, showing only what this player has already guessed."""
    puzzle = puzzles.get_or_create(date.today(), PuzzleKind.LEDGER)
    return Response(_ledger_state(_attempt_for(request.user, puzzle), puzzle))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ledger_guess(request):
    """Submit one five-letter guess."""
    puzzle = puzzles.get_or_create(date.today(), PuzzleKind.LEDGER)
    attempt = _attempt_for(request.user, puzzle)

    if attempt.finished:
        return Response({'error': "Today's board is already closed."}, status=400)

    guess = (request.data.get('word') or '').strip().upper()
    answer = puzzle.solution['word']

    if len(guess) != len(answer) or not guess.isalpha():
        return Response({'error': f'Enter a {len(answer)}-letter word.'}, status=400)
    if any(row['word'] == guess for row in attempt.guesses):
        return Response({'error': 'You already tried that one.'}, status=400)

    marks = games.mark_guess(guess, answer)
    attempt.guesses.append({'word': guess, 'marks': marks})

    solved = guess == answer
    used = len(attempt.guesses)

    if solved or used >= games.LEDGER_MAX_GUESSES:
        _complete(attempt, solved=solved, score=games.score_ledger(used, solved))
    else:
        attempt.save()

    return Response(_ledger_state(attempt, puzzle))


# --------------------------------------------------------------------------- #
# Rank It                                                                      #
# --------------------------------------------------------------------------- #

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def rank_board(request):
    """Read today's four companies, or submit an ordering."""
    puzzle = puzzles.get_or_create(date.today(), PuzzleKind.RANK)
    attempt = _attempt_for(request.user, puzzle)

    if request.method == 'POST':
        if attempt.finished:
            return Response({'error': "You have already ranked today's board."}, status=400)

        submitted = [str(symbol).upper() for symbol in request.data.get('order') or []]
        expected = {card['symbol'] for card in puzzle.payload['cards']}

        if set(submitted) != expected:
            return Response({'error': 'Order every company exactly once.'}, status=400)

        score, concordant, pairs = games.score_rank(submitted, puzzle.solution['order'])
        attempt.guesses.append({'order': submitted, 'pairs': concordant, 'of': pairs})
        _complete(attempt, solved=concordant == pairs, score=score)

    return Response(
        {
            **puzzle.payload,
            'finished': attempt.finished,
            'solved': attempt.solved,
            'score': attempt.score,
            'result': attempt.guesses[-1] if attempt.guesses else None,
            'answer': puzzle.solution if attempt.finished else None,
        }
    )
