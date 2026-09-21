"""Profile, onboarding and XP."""

from __future__ import annotations

from datetime import date

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from daily.models import Streak

from .models import DemoPortfolio, UserProfile

# Each answer contributes to a starting level, so an experienced user is not
# made to sit through "what is a savings account".
EXPERIENCE_POINTS = {'very_experienced': 3, 'experienced': 2, 'basics': 1, 'beginner': 0}
RISK_POINTS = {'aggressive': 2, 'balanced': 1, 'safe': 0}
COMMITTED_AMOUNTS = {'50k_2l', 'over_2l'}
LONG_HORIZON_GOALS = {'long_term_wealth', 'extra_income'}

# Starting XP is set to the unlock threshold for the level, so the courses a
# placement earns are immediately available.
PLACEMENTS = ((5, 'advanced', 1200), (3, 'intermediate', 750), (0, 'beginner', 50))


def _profile_for(user) -> UserProfile:
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def _serialise(profile: UserProfile) -> dict:
    streak, _ = Streak.objects.get_or_create(user=profile.user)

    return {
        'id': profile.user_id,
        'username': profile.user.username,
        'email': profile.user.email,
        'level': profile.level,
        'xp': profile.xp,
        'streak': streak.current,
        'confidence_score': profile.confidence_score,
        'financial_goal': profile.financial_goal,
        'investment_experience': profile.investment_experience,
        'risk_tolerance': profile.risk_tolerance,
        'initial_investment': profile.initial_investment,
        'timeline': profile.timeline,
        'needs_onboarding': not (profile.financial_goal and profile.risk_tolerance),
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    """The signed-in user's profile."""
    profile = _profile_for(request.user)
    profile.calculate_level_from_xp()
    profile.refresh_from_db()
    return Response(_serialise(profile))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_onboarding(request):
    """Record onboarding answers and place the learner at a starting level."""
    profile = _profile_for(request.user)

    for field in ('financial_goal', 'investment_experience', 'risk_tolerance',
                  'initial_investment', 'timeline'):
        value = request.data.get(field)
        if value:
            setattr(profile, field, value)

    score = (
        EXPERIENCE_POINTS.get(profile.investment_experience, 0)
        + RISK_POINTS.get(profile.risk_tolerance, 0)
        + (1 if profile.initial_investment in COMMITTED_AMOUNTS else 0)
        + (1 if profile.financial_goal in LONG_HORIZON_GOALS else 0)
    )

    level, starting_xp = next((lvl, xp) for threshold, lvl, xp in PLACEMENTS if score >= threshold)
    profile.level = level
    # Never reduce XP: re-running onboarding must not erase earned progress.
    profile.xp = max(profile.xp, starting_xp)
    profile.save()

    DemoPortfolio.objects.get_or_create(user=request.user)

    return Response({'success': True, 'placement_score': score, 'profile': _serialise(profile)})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def award_xp(request):
    """Award XP and report whether it caused a level-up."""
    try:
        amount = int(request.data.get('amount', 0))
    except (TypeError, ValueError):
        amount = 0

    # Capped so a client cannot mint arbitrary XP by replaying the endpoint.
    if not 0 < amount <= 500:
        return Response({'error': 'Amount must be between 1 and 500.'}, status=400)

    profile = _profile_for(request.user)
    before = profile.level

    profile.xp += amount
    profile.save(update_fields=['xp'])
    profile.calculate_level_from_xp()
    profile.refresh_from_db()

    _touch_streak(profile)

    return Response(
        {
            'success': True,
            'awarded': amount,
            'total_xp': profile.xp,
            'level': profile.level,
            'leveled_up': before != profile.level,
        }
    )


def _touch_streak(profile: UserProfile) -> None:
    """Keep the profile's streak mirror in step with the daily one."""
    streak, _ = Streak.objects.get_or_create(user=profile.user)
    streak.register(date.today())

    if profile.streak != streak.current:
        profile.streak = streak.current
        profile.last_activity_date = date.today()
        profile.save(update_fields=['streak', 'last_activity_date'])
