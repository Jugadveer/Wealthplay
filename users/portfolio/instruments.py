"""
The instruments goal mode adds: deposits and SIPs.

The normal practice account holds stocks, because learning to read a price and
size a position is what it is for. A goal-linked account holds the things a goal
is actually funded with — a deposit that cannot fall, a monthly instruction into
an index, gold as ballast. Trading a goal with stocks alone teaches the wrong
lesson about how goals get met.

Valuation is computed, never stored: a deposit is worth its principal compounded
for the days it has been open, and a SIP is worth its units at today's NAV. That
means nothing can drift out of sync with the market it is priced against.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.utils import timezone

from users.models import PracticeDeposit, PracticeSip

from .simulation import FUNDS, fund_nav

# Deposit rates by tenure. Longer money earns a little more, as it does anywhere.
FD_RATES = ((12, 0.0680), (24, 0.0700), (36, 0.0705), (60, 0.0710))

MIN_DEPOSIT = 1_000
MIN_SIP = 500


def fd_rate(tenure_months: int) -> float:
    """The rate for a tenure, using the longest band it qualifies for."""
    rate = FD_RATES[0][1]
    for months, value in FD_RATES:
        if tenure_months >= months:
            rate = value
    return rate


def deposit_value(deposit: PracticeDeposit, today: date | None = None) -> dict:
    """What a deposit is worth now, and what it will be worth at maturity."""
    today = today or timezone.localdate()
    principal = float(deposit.principal)
    rate = float(deposit.rate)

    days_held = max(0, (today - deposit.opened_on).days)
    term_days = deposit.tenure_months * 30
    accrual_days = min(days_held, term_days)

    current = principal * (1 + rate) ** (accrual_days / 365)
    at_maturity = principal * (1 + rate) ** (term_days / 365)
    matured = days_held >= term_days

    return {
        'id': deposit.id,
        'principal': round(principal, 2),
        'rate_percent': round(rate * 100, 2),
        'tenure_months': deposit.tenure_months,
        'opened_on': deposit.opened_on.isoformat(),
        'matures_in_days': max(0, term_days - days_held),
        'matured': matured,
        'current_value': round(current, 2),
        'value_at_maturity': round(at_maturity, 2),
        'interest_so_far': round(current - principal, 2),
    }


def break_value(deposit: PracticeDeposit, today: date | None = None) -> float:
    """What you get if you close it early: the reduced rate, as a bank would apply."""
    today = today or timezone.localdate()
    days_held = max(0, (today - deposit.opened_on).days)
    penalised = max(0.0, float(deposit.rate) - PracticeDeposit.BREAK_PENALTY)
    return round(float(deposit.principal) * (1 + penalised) ** (days_held / 365), 2)


def sip_value(sip: PracticeSip, today: date | None = None) -> dict:
    """What a SIP is worth, and what the averaging actually achieved."""
    nav = fund_nav(sip.instrument, today)
    invested = float(sip.invested)
    value = sip.units * nav

    return {
        'id': sip.id,
        'instrument': sip.instrument,
        'label': FUNDS.get(sip.instrument, {}).get('label', sip.instrument),
        'monthly_amount': float(sip.monthly_amount),
        'active': sip.active,
        'units': round(sip.units, 4),
        'nav': nav,
        'average_cost': round(invested / sip.units, 4) if sip.units else 0.0,
        'invested': round(invested, 2),
        'current_value': round(value, 2),
        'pnl': round(value - invested, 2),
        'pnl_percent': round((value / invested - 1) * 100, 2) if invested else 0.0,
        'last_run_on': sip.last_run_on.isoformat() if sip.last_run_on else None,
    }


def summarise(portfolio, today: date | None = None) -> dict:
    """Every non-stock holding, valued, for the portfolio view."""
    deposits = [deposit_value(d, today) for d in portfolio.deposits.filter(closed_on__isnull=True)]
    sips = [sip_value(s, today) for s in portfolio.sips.all()]

    return {
        'deposits': deposits,
        'sips': sips,
        'deposits_value': round(sum(d['current_value'] for d in deposits), 2),
        'sips_value': round(sum(s['current_value'] for s in sips), 2),
    }


def total_value(portfolio, today: date | None = None) -> Decimal:
    """What the deposits and SIPs add to the account total."""
    figures = summarise(portfolio, today)
    return Decimal(str(figures['deposits_value'] + figures['sips_value']))


def run_due_sips(portfolio, today: date | None = None) -> list[dict]:
    """Buy this month's instalment for every active SIP that has not run.

    Called when the monthly contribution is paid in, so the money arrives and is
    invested in one action — which is what a real SIP does and what makes the
    average cost meaningful.
    """
    today = today or timezone.localdate()
    executed = []

    for sip in portfolio.sips.filter(active=True):
        if sip.last_run_on and (sip.last_run_on.year, sip.last_run_on.month) == (today.year, today.month):
            continue

        amount = Decimal(str(sip.monthly_amount))
        if Decimal(str(portfolio.balance)) < amount:
            continue

        nav = fund_nav(sip.instrument, today)
        units = float(amount) / nav

        portfolio.balance = Decimal(str(portfolio.balance)) - amount
        sip.units += units
        sip.invested = Decimal(str(sip.invested)) + amount
        sip.last_run_on = today
        sip.save(update_fields=['units', 'invested', 'last_run_on'])

        executed.append({
            'instrument': sip.instrument,
            'amount': float(amount),
            'nav': nav,
            'units': round(units, 4),
        })

    if executed:
        portfolio.save(update_fields=['balance'])

    return executed
