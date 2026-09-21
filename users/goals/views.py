"""
Goal endpoints.

Views stay thin: parse, delegate to :mod:`planner`, respond. The only logic here
is the part that touches other parts of the app — linking a goal to the practice
account, and paying a monthly contribution into it.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ai import tutor

from ..models import DemoPortfolio, FinancialGoal
from ..portfolio.valuation import value_portfolio
from . import assessment, planner


def _parse_date(raw) -> date | None:
    try:
        return datetime.strptime(str(raw)[:10], '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return None


def _amount(raw, default: float = 0.0) -> float:
    try:
        return max(0.0, float(raw))
    except (TypeError, ValueError):
        return default


def _portfolio(user) -> DemoPortfolio:
    portfolio, _ = DemoPortfolio.objects.get_or_create(user=user)
    return portfolio


def _serialise(goal: FinancialGoal, account_value: float | None = None) -> dict:
    """One goal, with its plan attached.

    A linked goal reports the practice account as its progress, because that is
    literally where the money is: every trade moves the bar.
    """
    category = planner.category_for(goal.category)
    saved = float(goal.current_amount)

    if goal.linked and account_value is not None:
        saved = account_value

    plan = None
    if goal.target_date:
        plan = planner.build(
            target_amount=float(goal.target_amount),
            target_date=goal.target_date,
            saved=saved,
            monthly_capacity=float(goal.monthly_capacity),
            category_key=goal.category,
        )

    return {
        'id': goal.id,
        'title': goal.title,
        'category': category.key,
        'category_label': category.label,
        'icon': category.icon,
        'criticality': category.criticality,
        'target_amount': float(goal.target_amount),
        'current_amount': round(saved, 2),
        'progress_percent': (
            min(100, round(saved / float(goal.target_amount) * 100, 1))
            if goal.target_amount
            else 0
        ),
        'target_date': goal.target_date.isoformat() if goal.target_date else None,
        'monthly_capacity': float(goal.monthly_capacity),
        'plan_choice': goal.plan_choice,
        'linked': goal.linked,
        'plan': plan,
    }


# --------------------------------------------------------------------------- #
# Reading                                                                      #
# --------------------------------------------------------------------------- #

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_goals(request):
    """Every goal with its plan, plus the account the linked one draws from."""
    portfolio = _portfolio(request.user)
    account = value_portfolio(portfolio)

    goals = FinancialGoal.objects.filter(user=request.user).order_by('target_date', 'id')

    return Response({
        'goals': [_serialise(goal, account['total_value']) for goal in goals],
        'categories': [
            {
                'key': category.key,
                'label': category.label,
                'icon': category.icon,
                'criticality': category.criticality,
                'note': category.note,
            }
            for category in planner.CATEGORIES
        ],
        'account': {
            'total_value': account['total_value'],
            'balance': account['balance'],
            'monthly_contribution': float(portfolio.monthly_contribution),
            'total_contributed': float(portfolio.total_contributed),
            'last_contribution_on': (
                portfolio.last_contribution_on.isoformat()
                if portfolio.last_contribution_on
                else None
            ),
            'contribution_due': _contribution_due(portfolio),
        },
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assess_goal(request):
    """Read the goal and the person's finances, and put the risk choice to them.

    The classification and the capacity are computed here, deterministically, so
    the feature works with no model available. The model only phrases it — and
    when it is unavailable the response says so rather than passing a template
    off as advice.
    """
    description = (request.data.get('description') or '').strip()
    target_date = _parse_date(request.data.get('target_date'))
    target_amount = _amount(request.data.get('target_amount'))

    if not description:
        return Response({'error': 'Say what the goal is in your own words.'}, status=400)
    if not target_date or target_date <= date.today():
        return Response({'error': 'The target date has to be in the future.'}, status=400)
    if target_amount <= 0:
        return Response({'error': 'The target amount has to be more than zero.'}, status=400)

    category = assessment.classify(description)
    months = planner.months_until(target_date)

    income = _amount(request.data.get('monthly_income'))
    commitments = _amount(request.data.get('monthly_commitments'))
    dependants = int(_amount(request.data.get('dependants')))

    capacity = assessment.capacity(
        monthly_income=income,
        monthly_commitments=commitments,
        months=months,
        dependants=dependants,
        has_emergency_fund=bool(request.data.get('has_emergency_fund')),
        criticality=category.criticality,
    )

    observations = tutor.assess_goal(
        description=description,
        facts={
            'target_today': f'Rs {target_amount:,.0f}',
            'years_away': round(months / 12, 1),
            # Both units, because the guard checks any span of time an answer
            # quotes and a horizon written in months is not an invention.
            'months_away': months,
            'already_saved': f'Rs {_amount(request.data.get("current_amount")):,.0f}',
            'monthly_income': f'Rs {income:,.0f}',
            'monthly_commitments': f'Rs {commitments:,.0f}',
            'dependants': dependants,
        },
        capacity=capacity.as_dict(),
    )

    # The verdict is computed. The model only supplies the observations under
    # it, and only when every figure in them came from the user's own numbers.
    #
    # It used to write the headline and the stance too, and returned "The goal
    # is too ambitious and unrealistic" for a goal the same response marked
    # can_take_risk — two contradictory judgements on one screen.
    verdict = assessment.fallback_verdict(capacity, category)
    if observations:
        verdict = {**verdict, 'available': True, 'reasoning': observations}

    return Response({
        'assessment': {**verdict, 'capacity': capacity.as_dict(), 'category_label': category.label,
                       'icon': category.icon},
        'options': _appetite_options(capacity.level, category.criticality, months),
    })


def _appetite_options(level: str, criticality: str, months: int) -> list[dict]:
    """The choices to offer, and what each one means in plain words."""
    options = [
        {
            'key': 'safe',
            'label': 'Keep it safe',
            'detail': 'Nothing can fall. Costs the most each month.',
        },
        {
            'key': 'balanced',
            'label': 'Balanced',
            'detail': 'The most this goal and this horizon can reasonably carry.',
        },
    ]

    growth_allowed = months >= 60 and criticality != 'critical' and level == 'high'
    options.append({
        'key': 'growth',
        'label': 'Use the risk room',
        'detail': (
            'More equity, a lower monthly amount, a wider range of outcomes.'
            if growth_allowed
            else 'Not available for this goal — it cannot be postponed if markets are down.'
        ),
        'available': growth_allowed,
    })

    return options


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def preview_plan(request):
    """Plan a goal before committing to it, so the form can show live numbers."""
    target_date = _parse_date(request.data.get('target_date'))
    target_amount = _amount(request.data.get('target_amount'))

    if not target_date or target_amount <= 0:
        return Response({'error': 'A target amount and a target date are required.'}, status=400)
    if target_date <= date.today():
        return Response({'error': 'The target date has to be in the future.'}, status=400)

    return Response({
        'plan': planner.build(
            target_amount=target_amount,
            target_date=target_date,
            saved=_amount(request.data.get('current_amount')),
            monthly_capacity=_amount(request.data.get('monthly_capacity')),
            category_key=request.data.get('category') or 'general',
            appetite=request.data.get('appetite'),
        )
    })


# --------------------------------------------------------------------------- #
# Writing                                                                      #
# --------------------------------------------------------------------------- #

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_goal(request):
    """Create a goal from the form."""
    title = (request.data.get('title') or '').strip()
    target_date = _parse_date(request.data.get('target_date'))
    target_amount = _amount(request.data.get('target_amount'))

    if not title:
        return Response({'error': 'Give the goal a name.'}, status=400)
    if target_amount <= 0:
        return Response({'error': 'The target amount has to be more than zero.'}, status=400)
    if not target_date or target_date <= date.today():
        return Response({'error': 'The target date has to be in the future.'}, status=400)

    goal = FinancialGoal.objects.create(
        user=request.user,
        title=title,
        name=title,
        target_amount=Decimal(str(target_amount)),
        current_amount=Decimal(str(_amount(request.data.get('current_amount')))),
        monthly_capacity=Decimal(str(_amount(request.data.get('monthly_capacity')))),
        target_date=target_date,
        category=planner.category_for(request.data.get('category')).key,
        plan_choice=request.data.get('plan_choice') or 'balanced',
    )

    account = value_portfolio(_portfolio(request.user))
    return Response({'goal': _serialise(goal, account['total_value'])}, status=201)


@api_view(['PATCH', 'POST'])
@permission_classes([IsAuthenticated])
def update_goal(request, goal_id):
    """Edit a goal, including contributing towards it."""
    goal = FinancialGoal.objects.filter(id=goal_id, user=request.user).first()
    if goal is None:
        return Response({'error': 'That goal does not exist.'}, status=404)

    data = request.data
    if 'title' in data and str(data['title']).strip():
        goal.title = goal.name = str(data['title']).strip()
    if 'target_amount' in data:
        goal.target_amount = Decimal(str(_amount(data['target_amount'], float(goal.target_amount))))
    if 'current_amount' in data:
        goal.current_amount = Decimal(str(_amount(data['current_amount'])))
    if 'monthly_capacity' in data:
        goal.monthly_capacity = Decimal(str(_amount(data['monthly_capacity'])))
    if 'plan_choice' in data:
        goal.plan_choice = str(data['plan_choice'])
    if 'category' in data:
        goal.category = planner.category_for(data['category']).key
    if 'target_date' in data:
        parsed = _parse_date(data['target_date'])
        if parsed:
            goal.target_date = parsed

    goal.save()
    account = value_portfolio(_portfolio(request.user))
    return Response({'goal': _serialise(goal, account['total_value'])})


@api_view(['DELETE', 'POST'])
@permission_classes([IsAuthenticated])
def delete_goal(request, goal_id):
    deleted, _ = FinancialGoal.objects.filter(id=goal_id, user=request.user).delete()
    if not deleted:
        return Response({'error': 'That goal does not exist.'}, status=404)
    return Response({'success': True})


# --------------------------------------------------------------------------- #
# Goal-based trading                                                           #
# --------------------------------------------------------------------------- #

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def link_goal(request, goal_id):
    """Point the practice account at one goal, or unlink it.

    Only one goal may be linked, because the account is one pot of money and two
    goals both claiming it would each report progress that does not exist.
    """
    goal = FinancialGoal.objects.filter(id=goal_id, user=request.user).first()
    if goal is None:
        return Response({'error': 'That goal does not exist.'}, status=404)

    enable = bool(request.data.get('linked', True))

    if enable:
        FinancialGoal.objects.filter(user=request.user).exclude(id=goal.id).update(linked=False)
    goal.linked = enable
    goal.save(update_fields=['linked'])

    account = value_portfolio(_portfolio(request.user))
    return Response({'goal': _serialise(goal, account['total_value'])})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_contribution(request):
    """Set the monthly amount paid into the practice account."""
    portfolio = _portfolio(request.user)
    portfolio.monthly_contribution = Decimal(str(_amount(request.data.get('monthly_contribution'))))
    portfolio.save(update_fields=['monthly_contribution'])

    return Response({
        'monthly_contribution': float(portfolio.monthly_contribution),
        'contribution_due': _contribution_due(portfolio),
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pay_contribution(request):
    """Credit this month's contribution to the practice account.

    Once per calendar month, so clicking twice does not fund the account twice.
    A real SIP debits on a date; this is the same idea with the date being
    whenever the learner next opens the app.
    """
    portfolio = _portfolio(request.user)
    amount = portfolio.monthly_contribution

    if amount <= 0:
        return Response({'error': 'Set a monthly amount first.'}, status=400)
    if not _contribution_due(portfolio):
        return Response({'error': 'This month has already been paid in.'}, status=400)

    portfolio.balance = Decimal(str(portfolio.balance)) + amount
    portfolio.total_contributed = Decimal(str(portfolio.total_contributed)) + amount
    portfolio.last_contribution_on = date.today()
    portfolio.save(update_fields=['balance', 'total_contributed', 'last_contribution_on'])

    # The money arrives and is invested in one action, which is what a real SIP
    # does — and it is what makes the average cost mean anything.
    from ..portfolio import instruments

    executed = instruments.run_due_sips(portfolio)

    return Response({
        'success': True,
        'credited': float(amount),
        'sips_run': executed,
        'balance': float(portfolio.balance),
        'total_contributed': float(portfolio.total_contributed),
        'contribution_due': False,
    })


def _contribution_due(portfolio: DemoPortfolio) -> bool:
    """True when this calendar month has not been paid in yet."""
    if portfolio.monthly_contribution <= 0:
        return False

    last = portfolio.last_contribution_on
    today = date.today()
    return last is None or (last.year, last.month) != (today.year, today.month)
