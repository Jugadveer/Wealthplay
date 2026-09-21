"""
Achievements.

The catalogue is a declarative table and unlocking is one loop over it. The
previous version repeated the same eight-line ``get_or_create`` + grant-XP block
twenty times, which is how it ended up granting XP twice for trading
achievements: once inline, and again in a trailing "award XP" pass.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from simulator.models import QuizRun, UserScenarioAttempt

from .models import (
    Achievement,
    DemoPortfolio,
    StockPredictionChallenge,
    UserAchievement,
    UserProfile,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Rule:
    """One achievement: how it is described, and when it unlocks.

    ``unlocks_when`` receives a :class:`Progress` snapshot, so every rule reads
    as a single condition and no rule issues its own queries.
    """

    id: str
    name: str
    description: str
    icon: str
    category: str
    xp: int
    unlocks_when: Callable[['Progress'], bool]


@dataclass
class Progress:
    """Everything the rules need, gathered once."""

    xp: int
    streak: int
    holdings: int
    sectors: int
    has_traded: bool
    largest_position: float
    portfolio_return: float
    scenario_score: int
    perfect_scenarios: int
    correct_predictions: int
    modules_completed: int


CATALOGUE: tuple[Rule, ...] = (
    # Trading
    Rule('first_trade', 'First Trade', 'Execute your first trade', 'briefcase', 'trading', 25,
         lambda p: p.has_traded),
    Rule('risk_taker', 'Size Matters', 'Build a single position worth over ₹10,000', 'zap', 'trading', 50,
         lambda p: p.largest_position >= 10_000),
    Rule('portfolio_pro', 'Portfolio Pro', 'Hold five different stocks at once', 'layers', 'trading', 100,
         lambda p: p.holdings >= 5),
    Rule('diversified', 'Diversified', 'Hold stocks across three or more sectors', 'target', 'trading', 75,
         lambda p: p.sectors >= 3),
    Rule('profit_maker', 'In the Green', 'Reach a 10% return on your practice portfolio', 'trending-up', 'trading', 200,
         lambda p: p.portfolio_return >= 10),
    Rule('portfolio_master', 'Compounding', 'Reach a 25% return on your practice portfolio', 'trending-up', 'trading', 300,
         lambda p: p.portfolio_return >= 25),

    # Learning
    Rule('first_lesson', 'First Lesson', 'Finish your first module', 'book-open', 'learning', 20,
         lambda p: p.modules_completed >= 1),
    Rule('knowledge_seeker', 'Ten Down', 'Finish ten modules', 'library', 'learning', 200,
         lambda p: p.modules_completed >= 10),
    Rule('scenario_master', 'Scenario Master', 'Score 1,000 points across scenarios', 'compass', 'learning', 100,
         lambda p: p.scenario_score >= 1000),
    Rule('scenario_perfect', 'Flawless', 'Score full marks on a scenario run', 'check-circle-2', 'learning', 100,
         lambda p: p.perfect_scenarios >= 1),

    # Markets
    Rule('stock_predictor', 'Ten Calls', 'Get ten market calls right', 'activity', 'markets', 75,
         lambda p: p.correct_predictions >= 10),
    Rule('stock_master', 'Market Read', 'Get fifty market calls right', 'radar', 'markets', 200,
         lambda p: p.correct_predictions >= 50),

    # Consistency
    Rule('streak_5', 'Five Days', 'Show up five days running', 'flame', 'consistency', 50,
         lambda p: p.streak >= 5),
    Rule('streak_10', 'Ten Days', 'Show up ten days running', 'flame', 'consistency', 100,
         lambda p: p.streak >= 10),
    Rule('streak_30', 'A Month', 'Show up thirty days running', 'flame', 'consistency', 300,
         lambda p: p.streak >= 30),

    # Milestones
    Rule('xp_100', 'Getting Started', 'Earn 100 XP', 'sparkles', 'milestone', 25,
         lambda p: p.xp >= 100),
    Rule('xp_500', 'Five Hundred', 'Earn 500 XP', 'sparkles', 'milestone', 50,
         lambda p: p.xp >= 500),
    Rule('xp_1000', 'Four Figures', 'Earn 1,000 XP', 'trophy', 'milestone', 150,
         lambda p: p.xp >= 1000),
    Rule('xp_2500', 'Seasoned', 'Earn 2,500 XP', 'crown', 'milestone', 250,
         lambda p: p.xp >= 2500),
)


# --------------------------------------------------------------------------- #
# Evaluation                                                                   #
# --------------------------------------------------------------------------- #

def _snapshot(user) -> Progress:
    """Gather every signal the rules read."""
    from courses.models import UserCourseProgress
    from users.portfolio import value_portfolio

    profile, _ = UserProfile.objects.get_or_create(user=user)

    holdings_count = sectors = 0
    largest_position = portfolio_return = 0.0
    has_traded = False

    portfolio = DemoPortfolio.objects.filter(user=user).first()
    if portfolio:
        trades = portfolio.trade_history if isinstance(portfolio.trade_history, list) else []
        # A sold-out position still counts: the trade happened.
        has_traded = bool(portfolio.holdings) or len(trades) > 1

        valued = value_portfolio(portfolio)
        holdings = valued['holdings']
        holdings_count = len(holdings)
        sectors = len({h.get('sector') for h in holdings if h.get('sector')})
        portfolio_return = valued['total_pnl_percent']
        largest_position = max((h['invested'] for h in holdings), default=0.0)

    scenario_score = sum(
        UserScenarioAttempt.objects.filter(user=user).values_list('score_earned', flat=True)
    )

    return Progress(
        xp=profile.xp,
        streak=profile.streak,
        holdings=holdings_count,
        sectors=sectors,
        has_traded=has_traded,
        largest_position=largest_position,
        portfolio_return=portfolio_return,
        scenario_score=scenario_score,
        perfect_scenarios=_perfect_scenario_count(user),
        correct_predictions=StockPredictionChallenge.objects.filter(user=user, is_correct=True).count(),
        modules_completed=UserCourseProgress.objects.filter(user=user, status='completed')
        .exclude(module_id='')
        .count(),
    )


def _perfect_scenario_count(user) -> int:
    """Completed scenario runs where every decision scored full marks."""
    perfect = 0
    for run in QuizRun.objects.filter(user=user, is_completed=True):
        try:
            scenarios = run.get_scenario_list()
        except (TypeError, ValueError):
            logger.debug('skipping malformed quiz run %s', run.id)
            continue
        if scenarios and run.total_score >= len(scenarios) * 20:
            perfect += 1
    return perfect


def check_and_unlock_achievements(user) -> list[Achievement]:
    """Unlock everything the user now qualifies for; return what was new.

    Safe to call repeatedly: ``get_or_create`` makes each unlock idempotent and
    XP is granted exactly once, at the moment of unlocking.
    """
    progress = _snapshot(user)
    already = set(UserAchievement.objects.filter(user=user).values_list('achievement_id', flat=True))

    newly: list[Achievement] = []
    earned_xp = 0

    for rule in CATALOGUE:
        if rule.id in already:
            continue

        try:
            qualifies = rule.unlocks_when(progress)
        except Exception:
            logger.warning('achievement rule %s failed to evaluate', rule.id, exc_info=True)
            continue

        if not qualifies:
            continue

        achievement = _sync_definition(rule)
        _, created = UserAchievement.objects.get_or_create(user=user, achievement=achievement)
        if created:
            newly.append(achievement)
            earned_xp += rule.xp

    if earned_xp:
        UserProfile.objects.filter(user=user).update(xp=progress.xp + earned_xp)

    return newly


def _sync_definition(rule: Rule) -> Achievement:
    """Create or refresh the stored row so CATALOGUE stays the source of truth."""
    fields = {
        'name': rule.name,
        'description': rule.description,
        'icon_name': rule.icon,
        'category': rule.category,
        'xp_reward': rule.xp,
        'is_active': True,
    }

    achievement, created = Achievement.objects.get_or_create(id=rule.id, defaults=fields)
    if not created and any(getattr(achievement, key) != value for key, value in fields.items()):
        for key, value in fields.items():
            setattr(achievement, key, value)
        achievement.save()

    return achievement


# --------------------------------------------------------------------------- #
# Endpoints                                                                    #
# --------------------------------------------------------------------------- #

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_achievements(request):
    """The full catalogue with this user's unlock state.

    Re-evaluates on read. Evaluation used to be throttled to once per ten
    minutes via the session, so a user could earn an achievement and still see
    it locked — which is exactly what happened after a first trade.
    """
    check_and_unlock_achievements(request.user)

    unlocked = {
        ua.achievement_id: ua.unlocked_at
        for ua in UserAchievement.objects.filter(user=request.user, unlocked_at__isnull=False)
    }

    catalogue = [
        {
            'id': rule.id,
            'name': rule.name,
            'description': rule.description,
            'icon_name': rule.icon,
            'category': rule.category,
            'xp_reward': rule.xp,
            'unlocked': rule.id in unlocked,
            'unlocked_at': unlocked[rule.id].isoformat() if rule.id in unlocked else None,
        }
        for rule in CATALOGUE
    ]

    return Response(
        {
            'achievements': catalogue,
            'total_unlocked': sum(1 for row in catalogue if row['unlocked']),
            'total_available': len(catalogue),
        }
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_achievements(request):
    """Force a re-check. Called after an XP event, never on page mount."""
    newly = check_and_unlock_achievements(request.user)

    return Response(
        {
            'newly_unlocked': [
                {
                    'id': a.id,
                    'name': a.name,
                    'description': a.description,
                    'icon_name': a.icon_name,
                    'xp_reward': a.xp_reward,
                }
                for a in newly
            ],
            'count': len(newly),
        }
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_achievement_notified(request):
    """Record that the unlock popup has been shown."""
    achievement_id = request.data.get('achievement_id')
    if not achievement_id:
        return Response({'error': 'achievement_id is required.'}, status=400)

    updated = UserAchievement.objects.filter(
        user=request.user, achievement_id=achievement_id
    ).update(notified=True)

    if not updated:
        return Response({'error': 'That achievement is not unlocked.'}, status=404)
    return Response({'success': True})
