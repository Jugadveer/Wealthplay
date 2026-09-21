"""
Endpoints for the instruments that only exist in goal mode.

Gated deliberately. The normal practice account is stocks, because reading a
price and sizing a position is what it is for. Deposits and SIPs appear once a
goal is linked, because that is when "how do I actually fund this" becomes the
question — and offering a fixed deposit to somebody with no goal is offering an
answer to nothing.
"""

from __future__ import annotations

from decimal import Decimal

from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import FinancialGoal, PracticeDeposit, PracticeSip
from . import instruments
from .simulation import FUNDS, fund_nav
from .views import _portfolio_for


def _goal_mode(user) -> FinancialGoal | None:
    return FinancialGoal.objects.filter(user=user, linked=True).first()


def _amount(raw, default: float = 0.0) -> float:
    try:
        return max(0.0, float(raw))
    except (TypeError, ValueError):
        return default


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_instruments(request):
    """Everything held besides stocks, plus what is available to open."""
    portfolio = _portfolio_for(request.user)
    goal = _goal_mode(request.user)

    return Response({
        'goal_mode': goal is not None,
        'goal': {'id': goal.id, 'title': goal.title} if goal else None,
        **instruments.summarise(portfolio),
        'available': {
            'deposit_rates': [
                {'tenure_months': months, 'rate_percent': round(rate * 100, 2)}
                for months, rate in instruments.FD_RATES
            ],
            'funds': [
                {'key': key, 'label': profile['label'], 'nav': fund_nav(key)}
                for key, profile in FUNDS.items()
            ],
            'min_deposit': instruments.MIN_DEPOSIT,
            'min_sip': instruments.MIN_SIP,
        },
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def open_deposit(request):
    """Lock cash into a fixed deposit."""
    if _goal_mode(request.user) is None:
        return Response(
            {'error': 'Deposits are part of goal mode. Link a goal to the practice account first.'},
            status=400,
        )

    portfolio = _portfolio_for(request.user)
    principal = _amount(request.data.get('principal'))
    tenure = int(_amount(request.data.get('tenure_months'), 12))

    if principal < instruments.MIN_DEPOSIT:
        return Response(
            {'error': f'The smallest deposit is {instruments.MIN_DEPOSIT:,} rupees.'}, status=400
        )
    if Decimal(str(portfolio.balance)) < Decimal(str(principal)):
        return Response({'error': f'Only {portfolio.balance:,.2f} is available.'}, status=400)

    deposit = PracticeDeposit.objects.create(
        portfolio=portfolio,
        principal=Decimal(str(principal)),
        rate=Decimal(str(instruments.fd_rate(tenure))),
        tenure_months=tenure,
    )
    portfolio.balance = Decimal(str(portfolio.balance)) - Decimal(str(principal))
    portfolio.save(update_fields=['balance'])

    return Response(
        {
            'success': True,
            'deposit': instruments.deposit_value(deposit),
            'balance': float(portfolio.balance),
        },
        status=201,
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def close_deposit(request, deposit_id):
    """Close a deposit — at full value if matured, at the penalised rate if not."""
    portfolio = _portfolio_for(request.user)
    deposit = PracticeDeposit.objects.filter(
        id=deposit_id, portfolio=portfolio, closed_on__isnull=True
    ).first()

    if deposit is None:
        return Response({'error': 'That deposit is not open.'}, status=404)

    figures = instruments.deposit_value(deposit)
    matured = figures['matured']
    proceeds = figures['current_value'] if matured else instruments.break_value(deposit)

    deposit.closed_on = timezone.localdate()
    deposit.broken_early = not matured
    deposit.save(update_fields=['closed_on', 'broken_early'])

    portfolio.balance = Decimal(str(portfolio.balance)) + Decimal(str(proceeds))
    portfolio.save(update_fields=['balance'])

    return Response({
        'success': True,
        'proceeds': proceeds,
        'broken_early': not matured,
        'lost_to_penalty': round(figures['current_value'] - proceeds, 2) if not matured else 0,
        'balance': float(portfolio.balance),
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_sip(request):
    """Set up a monthly instruction into one of the funds."""
    if _goal_mode(request.user) is None:
        return Response(
            {'error': 'SIPs are part of goal mode. Link a goal to the practice account first.'},
            status=400,
        )

    instrument = request.data.get('instrument')
    amount = _amount(request.data.get('monthly_amount'))

    if instrument not in FUNDS:
        return Response({'error': 'Pick one of the available funds.'}, status=400)
    if amount < instruments.MIN_SIP:
        return Response(
            {'error': f'The smallest SIP is {instruments.MIN_SIP:,} rupees a month.'}, status=400
        )

    portfolio = _portfolio_for(request.user)
    sip, created = PracticeSip.objects.get_or_create(
        portfolio=portfolio,
        instrument=instrument,
        defaults={'monthly_amount': Decimal(str(amount))},
    )

    if not created:
        sip.monthly_amount = Decimal(str(amount))
        sip.active = True
        sip.save(update_fields=['monthly_amount', 'active'])

    return Response(
        {'success': True, 'sip': instruments.sip_value(sip)},
        status=201 if created else 200,
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def stop_sip(request, sip_id):
    """Stop future instalments. Units already bought stay invested."""
    sip = PracticeSip.objects.filter(id=sip_id, portfolio__user=request.user).first()
    if sip is None:
        return Response({'error': 'That SIP does not exist.'}, status=404)

    sip.active = False
    sip.save(update_fields=['active'])
    return Response({'success': True, 'sip': instruments.sip_value(sip)})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def run_sips(request):
    """Buy this month's instalments now."""
    portfolio = _portfolio_for(request.user)
    executed = instruments.run_due_sips(portfolio)

    if not executed:
        return Response({'error': 'Nothing is due this month, or the cash is short.'}, status=400)

    return Response({'success': True, 'executed': executed, 'balance': float(portfolio.balance)})
