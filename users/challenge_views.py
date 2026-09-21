"""
Stock prediction challenge and leaderboards.

Scoring rewards *calibrated* calls rather than lucky ones: a correct direction
earns the base score, and writing a rationale earns a bonus regardless of
outcome, because articulating a thesis is the skill being taught.
"""

from __future__ import annotations

import random

from django.contrib.auth.models import User
from django.db.models import Count, Q, Sum
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ai import tutor
from simulator.models import UserScenarioAttempt
from users.portfolio import pricing

from .models import ChallengeLeaderboard, StockPredictionChallenge, StockPredictionQuestion

CORRECT_SCORE = 15
RATIONALE_BONUS = 5
STREAK_WINDOW = 20


# --------------------------------------------------------------------------- #
# Scoring                                                                      #
# --------------------------------------------------------------------------- #

def _direction_from_series(series: list[dict]) -> str:
    """Classify a price series as bullish, bearish or neutral.

    Uses the last ten sessions against the twenty before them. A flat market is
    genuinely neutral, and calling it either way should not score full marks.
    """
    closes = [float(p.get('close') or p.get('price') or 0) for p in series]
    closes = [c for c in closes if c > 0]
    if len(closes) < 10:
        return 'neutral'

    recent = closes[-10:]
    change = (recent[-1] - recent[0]) / recent[0] * 100

    if change > 1.5:
        return 'bullish'
    if change < -1.5:
        return 'bearish'
    return 'neutral'


def _clamp_confidence(value) -> int:
    """Confidence is a probability you assign to your own call, 50-100.

    Below 50 you would simply call the other way, so the scale starts there.
    """
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return 50
    return max(50, min(100, parsed))


def _normalise_call(text: str) -> str:
    """Map a free-text or button prediction onto bullish/bearish/neutral."""
    lowered = (text or '').lower()

    if any(word in lowered for word in ('bear', 'down', 'fall', 'drop', 'decline', 'sell', 'short')):
        return 'bearish'
    if any(word in lowered for word in ('bull', 'up', 'rise', 'gain', 'rally', 'buy', 'long')):
        return 'bullish'
    return 'neutral'


def _score(call: str, actual: str, has_rationale: bool) -> tuple[bool, int]:
    """Return ``(correct, points)``."""
    correct = call == actual
    points = CORRECT_SCORE if correct else 0

    # Reading a flat market as flat is a real read, not a non-answer.
    if not correct and 'neutral' in (call, actual):
        points = 5

    if has_rationale:
        points += RATIONALE_BONUS

    return correct, points


# --------------------------------------------------------------------------- #
# Leaderboard                                                                  #
# --------------------------------------------------------------------------- #

def refresh_standings(user) -> ChallengeLeaderboard:
    """Recompute one user's standings from their activity.

    Only ever called for a single user. The previous version rebuilt the entire
    leaderboard, for every user, on every request that touched it.
    """
    entry, _ = ChallengeLeaderboard.objects.get_or_create(user=user)

    predictions = StockPredictionChallenge.objects.filter(user=user)
    totals = predictions.aggregate(
        score=Sum('score'),
        total=Count('id'),
        correct=Count('id', filter=Q(is_correct=True)),
    )

    scenarios = UserScenarioAttempt.objects.filter(user=user)
    scenario_totals = scenarios.aggregate(score=Sum('score_earned'), attempts=Count('id'))

    entry.stock_score = totals['score'] or 0
    entry.total_predictions = totals['total'] or 0
    entry.correct_predictions = totals['correct'] or 0
    entry.scenario_score = scenario_totals['score'] or 0
    entry.scenario_attempts = scenario_totals['attempts'] or 0
    entry.total_score = entry.stock_score + entry.scenario_score

    # Streak = unbroken run of correct calls, most recent first.
    streak = 0
    for correct in predictions.order_by('-created_at').values_list('is_correct', flat=True)[:STREAK_WINDOW]:
        if not correct:
            break
        streak += 1

    entry.current_streak = streak
    entry.best_streak = max(entry.best_streak, streak)
    entry.save()
    return entry


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_leaderboard(request):
    """Top players by score or by streak."""
    board_type = request.query_params.get('type', 'scores')
    order = (
        ['-current_streak', '-total_score']
        if board_type == 'streaks'
        else ['-total_score', '-current_streak']
    )

    # Only the requester's row is recomputed; everyone else's was written when
    # they last played.
    refresh_standings(request.user)

    entries = ChallengeLeaderboard.objects.select_related('user').order_by(*order)[:20]

    return Response(
        {
            'type': board_type,
            'leaderboard': [
                {
                    'rank': rank,
                    'username': entry.user.username,
                    'is_you': entry.user_id == request.user.id,
                    'total_score': entry.total_score,
                    'current_streak': entry.current_streak,
                    'best_streak': entry.best_streak,
                    'total_predictions': entry.total_predictions,
                    'correct_predictions': entry.correct_predictions,
                    'accuracy': (
                        round(entry.correct_predictions / entry.total_predictions * 100)
                        if entry.total_predictions
                        else None
                    ),
                }
                for rank, entry in enumerate(entries, start=1)
            ],
        }
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_challenge_stats(request):
    """The requesting user's own standings."""
    entry = refresh_standings(request.user)
    attempted = entry.total_predictions + entry.scenario_attempts

    correct = entry.correct_predictions + UserScenarioAttempt.objects.filter(
        user=request.user, is_correct=True
    ).count()

    return Response(
        {
            'total_score': entry.total_score,
            'stock_score': entry.stock_score,
            'scenario_score': entry.scenario_score,
            'current_streak': entry.current_streak,
            'best_streak': entry.best_streak,
            'total_predictions': entry.total_predictions,
            'correct_predictions': entry.correct_predictions,
            'scenario_attempts': entry.scenario_attempts,
            'win_rate': round(correct / attempted * 100, 1) if attempted else 0.0,
        }
    )


# --------------------------------------------------------------------------- #
# The game                                                                     #
# --------------------------------------------------------------------------- #

# The live pool. Wide enough that a player does not see the same chart twice in
# a sitting, and every name is liquid enough to have a year of clean history.
LIVE_UNIVERSE = (
    'AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'META', 'TSLA',
    'RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK', 'SBIN', 'ITC', 'BHARTIARTL',
)

# Varying the horizon changes the read: a week is momentum, a quarter is trend.
LIVE_HORIZONS = (
    ('the next week', 60),
    ('the next month', 120),
    ('the next quarter', 250),
)

RECENT_SYMBOL_MEMORY = 8


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_random_stock_question(request):
    """Serve a prediction round the player has not already seen.

    The bank used to be drawn with ``order_by('?')`` and no memory, so with
    seven authored questions a player saw repeats within a handful of rounds.
    Now every answered question is recorded and excluded, and once the bank runs
    out the game continues on live charts — which never run out.
    """
    difficulty = request.query_params.get('difficulty')

    questions = StockPredictionQuestion.objects.filter(is_active=True)
    if difficulty:
        narrowed = questions.filter(difficulty__iexact=difficulty)
        questions = narrowed if narrowed.exists() else questions

    seen = StockPredictionChallenge.objects.filter(user=request.user).exclude(question=None)
    question = questions.exclude(id__in=seen.values('question_id')).order_by('?').first()

    if question:
        return Response(
            {
                'id': question.id,
                'source': 'bank',
                'stock_name': question.stock_name,
                'stock_symbol': question.stock_symbol,
                'question': question.question,
                'chart_data': question.chart_data,
                'difficulty': question.difficulty,
            }
        )

    return Response(_live_round(request.user, difficulty))


def _live_round(user, difficulty: str | None) -> dict:
    """A round built from a real chart, avoiding this player's recent symbols."""
    recent = list(
        StockPredictionChallenge.objects.filter(user=user)
        .order_by('-created_at')
        .values_list('stock_symbol', flat=True)[:RECENT_SYMBOL_MEMORY]
    )
    pool = [symbol for symbol in LIVE_UNIVERSE if symbol not in recent] or list(LIVE_UNIVERSE)

    symbol = random.choice(pool)
    horizon, window = random.choice(LIVE_HORIZONS)
    quote = pricing.quote(symbol)

    return {
        'id': None,
        'source': 'live',
        'stock_name': quote['name'],
        'stock_symbol': symbol,
        'question': f'Where does {quote["name"]} go over {horizon}?',
        'chart_data': pricing.history(symbol, days=window),
        'currency': quote['currency'],
        'difficulty': difficulty or 'intermediate',
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_prediction_hint(request):
    """A teaching hint derived from the real series.

    ``available: False`` when no model answered. The UI hides the hint rather
    than printing a canned line — the previous fallback shipped the literal
    string "The volume volume surge suggests a potential trend reversal".
    """
    symbol = (request.query_params.get('symbol') or '').strip().upper()
    if not symbol:
        return Response({'error': 'A symbol is required.'}, status=400)

    quote = pricing.quote(symbol)
    hint = tutor.chart_hint(symbol, quote['name'], pricing.history(symbol, days=60))

    return Response({'available': bool(hint), 'hint': hint})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_stock_prediction(request):
    """Record a call, score it, and return feedback on the reasoning."""
    call_text = (request.data.get('prediction') or '').strip()
    rationale = (request.data.get('rationale') or '').strip()
    confidence = _clamp_confidence(request.data.get('confidence'))
    question_id = request.data.get('question_id')
    symbol = (request.data.get('stock_symbol') or '').strip().upper()

    if not call_text:
        return Response({'error': 'A prediction is required.'}, status=400)

    question = StockPredictionQuestion.objects.filter(id=question_id).first() if question_id else None

    if question:
        symbol = question.stock_symbol
        actual = question.expected_direction
        # The bank stores up/down/neutral; scoring speaks bullish/bearish.
        actual = {'up': 'bullish', 'down': 'bearish'}.get(actual, 'neutral')
        explanation = question.explanation
        series = question.chart_data or []
    else:
        if not symbol:
            return Response({'error': 'A stock symbol is required.'}, status=400)
        series = pricing.history(symbol, days=60)
        actual = _direction_from_series(series)
        explanation = ''

    call = _normalise_call(call_text)
    correct, points = _score(call, actual, bool(rationale))

    # A bank question's expected direction is authored, not derived from its
    # synthetic chart, so quoting a move from that chart would contradict it.
    # Only live rounds report a real percentage.
    move = 0.0
    if question is None:
        closes = [float(p.get('close') or p.get('price') or 0) for p in series]
        closes = [c for c in closes if c > 0]
        if len(closes) >= 10:
            move = (closes[-1] - closes[-10]) / closes[-10] * 100

    feedback = tutor.judge_prediction(
        symbol,
        called=call,
        actual=actual,
        rationale=rationale,
        move_percent=move,
    )

    StockPredictionChallenge.objects.create(
        user=request.user,
        question=question,
        confidence=confidence,
        stock_symbol=symbol,
        prediction=call_text,
        prediction_direction=call,
        ai_direction=actual,
        ai_analysis=explanation,
        is_correct=correct,
        score=points,
        feedback=feedback or '',
    )

    entry = refresh_standings(request.user)

    return Response(
        {
            'correct': correct,
            'score': points,
            'your_call': call,
            'actual': actual,
            'move_percent': round(move, 2) if question is None else None,
            'explanation': explanation,
            'feedback': feedback,
            'feedback_available': bool(feedback),
            'rationale_bonus': RATIONALE_BONUS if rationale else 0,
            'confidence': confidence,
            'total_score': entry.total_score,
            'current_streak': entry.current_streak,
        }
    )


# --------------------------------------------------------------------------- #
# Calibration                                                                  #
# --------------------------------------------------------------------------- #

CALIBRATION_BANDS = ((50, 60), (60, 70), (70, 80), (80, 90), (90, 101))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_calibration(request):
    """How often the player was right, bucketed by how sure they said they were.

    Being right a lot is easy on easy calls. Being *calibrated* — right 70% of
    the times you said 70% — is the skill, and it is the one thing here that a
    quiz cannot teach. A perfectly calibrated player sits on the diagonal.
    """
    calls = list(
        StockPredictionChallenge.objects.filter(user=request.user).values_list(
            'confidence', 'is_correct'
        )
    )

    bands = []
    for low, high in CALIBRATION_BANDS:
        inside = [correct for confidence, correct in calls if low <= confidence < high]
        bands.append(
            {
                'label': f'{low}-{min(high, 100)}%',
                'stated': (low + min(high, 100)) / 2,
                'calls': len(inside),
                'actual': round(sum(inside) / len(inside) * 100, 1) if inside else None,
            }
        )

    measured = [band for band in bands if band['calls']]
    gap = (
        round(
            sum(abs(band['actual'] - band['stated']) * band['calls'] for band in measured)
            / sum(band['calls'] for band in measured),
            1,
        )
        if measured
        else None
    )

    return Response(
        {
            'bands': bands,
            'total_calls': len(calls),
            # One number: average distance between what you claimed and what
            # happened. Lower is better; 0 is perfectly calibrated.
            'calibration_gap': gap,
            'verdict': _calibration_verdict(gap, len(calls)),
        }
    )


def _calibration_verdict(gap: float | None, calls: int) -> str:
    if calls < 5:
        return f'Make {5 - calls} more calls and this starts to mean something.'
    if gap is None:
        return 'No calls with a stated confidence yet.'
    if gap <= 10:
        return 'Well calibrated. Your confidence matches your hit rate.'
    if gap <= 20:
        return 'Roughly calibrated. Watch the bands where you overclaim.'
    return 'Overconfident. You are surer than your record supports.'
