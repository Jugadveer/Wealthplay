"""
Turning a goal into a plan someone can actually follow.

A goal is four numbers — what it costs, when you need it, what you have, and
what you can put aside each month — and any plan is a claim about how to get
from the first three to the fourth. This module makes that claim explicit.

Two rules shape every plan it produces.

**The horizon chooses the instrument.** Money needed inside three years does not
belong in equity, because equity can be down 30% on the exact day you need it
and a school fee does not reschedule. Beyond seven years the reverse is true:
holding cash for a decade is a guaranteed real loss.

**What the goal is for changes how much risk it may carry.** A holiday that
slips by six months costs nothing. A child's fees in the year they are due
cannot slip at all. So the same horizon produces a more conservative plan for a
critical goal than for a discretionary one — which is the part most calculators
leave out.

Every figure here is nominal and pre-tax unless stated. Rates are the
assumptions in ``RETURNS`` and are stated back to the user rather than hidden.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

# Assumed annual returns. Conservative on equity relative to the twenty-year
# Nifty average, because a plan that only works at the historical best case is
# not a plan.
RETURNS = {
    'savings': 0.030,
    'fd': 0.068,
    'debt_fund': 0.072,
    'ppf': 0.071,
    'gold': 0.085,
    'equity': 0.110,
}

# What an equity allocation can plausibly do to a portfolio in a bad year. Used
# to show the downside of each plan rather than only its expected value.
EQUITY_DRAWDOWN = 0.35

INFLATION = 0.06
EDUCATION_INFLATION = 0.10


@dataclass(frozen=True)
class Category:
    """A kind of goal, and how much risk it is allowed to carry."""

    key: str
    label: str
    icon: str
    criticality: str  # critical | important | flexible
    inflation: float = INFLATION
    borrowable: bool = False  # can this normally be part-funded with a loan?
    note: str = ''


CATEGORIES: tuple[Category, ...] = (
    Category('emergency', 'Emergency fund', 'shield', 'critical', borrowable=False,
             note='Six months of expenses, reachable the same day. This one is never invested.'),
    Category('education', 'Child education', 'graduation-cap', 'critical',
             inflation=EDUCATION_INFLATION, borrowable=True,
             note='Education inflation runs near 10%, so the target moves faster than the market.'),
    Category('retirement', 'Retirement', 'sunset', 'critical', borrowable=False,
             note='The one goal nobody will lend you money for.'),
    Category('home', 'Home deposit', 'home', 'important', borrowable=True,
             note='The deposit is the goal; the rest is a loan with its own arithmetic.'),
    Category('wedding', 'Wedding', 'heart', 'important', borrowable=True),
    Category('business', 'Business capital', 'briefcase', 'important', borrowable=True),
    Category('car', 'Vehicle', 'car', 'flexible', borrowable=True,
             note='A depreciating asset. Borrowing for it costs twice.'),
    Category('travel', 'Travel', 'plane', 'flexible', borrowable=False),
    Category('gadget', 'Something you want', 'gift', 'flexible', borrowable=False),
    Category('general', 'General saving', 'wallet', 'important', borrowable=False),
)

BY_KEY = {category.key: category for category in CATEGORIES}
DEFAULT_CATEGORY = BY_KEY['general']


def category_for(key: str) -> Category:
    return BY_KEY.get((key or '').lower(), DEFAULT_CATEGORY)


# --------------------------------------------------------------------------- #
# The arithmetic                                                               #
# --------------------------------------------------------------------------- #

def months_until(target: date, today: date | None = None) -> int:
    """Whole months between now and the target date, floored at one."""
    today = today or date.today()
    months = (target.year - today.year) * 12 + (target.month - today.month)
    return max(1, months)


def future_value(present: float, annual_rate: float, months: int) -> float:
    """What a lump sum becomes, compounded monthly."""
    return present * (1 + annual_rate / 12) ** months


def sip_future_value(monthly: float, annual_rate: float, months: int) -> float:
    """What a monthly contribution becomes, invested at the start of each month."""
    rate = annual_rate / 12
    if rate == 0:
        return monthly * months
    return monthly * (((1 + rate) ** months - 1) / rate) * (1 + rate)


def sip_required(target: float, annual_rate: float, months: int, present: float = 0.0) -> float:
    """The monthly amount needed to reach ``target``, given what is already saved."""
    shortfall = target - future_value(present, annual_rate, months)
    if shortfall <= 0:
        return 0.0

    rate = annual_rate / 12
    if rate == 0:
        return shortfall / months
    return shortfall / ((((1 + rate) ** months - 1) / rate) * (1 + rate))


def inflate(amount: float, annual_rate: float, months: int) -> float:
    """What something costing ``amount`` today will cost then."""
    return amount * (1 + annual_rate) ** (months / 12)


def emi(principal: float, annual_rate: float, years: int) -> dict:
    """Monthly instalment, total repaid and total interest on a loan."""
    months = max(1, years * 12)
    rate = annual_rate / 12

    if rate == 0:
        instalment = principal / months
    else:
        factor = (1 + rate) ** months
        instalment = principal * rate * factor / (factor - 1)

    total = instalment * months
    return {
        'principal': round(principal, 2),
        'rate_percent': round(annual_rate * 100, 2),
        'years': years,
        'monthly': round(instalment, 2),
        'total_repaid': round(total, 2),
        'total_interest': round(total - principal, 2),
    }


# --------------------------------------------------------------------------- #
# Allocation                                                                   #
# --------------------------------------------------------------------------- #

# Equity share by horizon, before the goal's criticality is applied.
HORIZON_EQUITY = (
    (36, 0.00),
    (60, 0.30),
    (84, 0.50),
    (120, 0.65),
    (10_000, 0.75),
)

# How much of that equity a goal of each criticality is allowed to keep.
CRITICALITY_FACTOR = {'critical': 0.60, 'important': 0.85, 'flexible': 1.00}


def equity_share(months: int, criticality: str) -> float:
    """The equity weight this goal can carry, given its horizon and what it is for."""
    base = next(share for limit, share in HORIZON_EQUITY if months <= limit)
    return round(base * CRITICALITY_FACTOR.get(criticality, 0.85), 2)


def blended_return(equity: float) -> float:
    """Expected return of an equity/debt mix, using the debt-fund rate for the rest."""
    return equity * RETURNS['equity'] + (1 - equity) * RETURNS['debt_fund']


@dataclass
class Plan:
    """One way of funding the goal."""

    key: str
    label: str
    summary: str
    equity: float
    expected_return: float
    monthly_required: float
    projected: float
    downside: float
    allocation: list[dict] = field(default_factory=list)
    caution: str = ''

    def as_dict(self) -> dict:
        return {
            'key': self.key,
            'label': self.label,
            'summary': self.summary,
            'equity_percent': round(self.equity * 100),
            'expected_return_percent': round(self.expected_return * 100, 1),
            'monthly_required': round(self.monthly_required),
            'projected': round(self.projected),
            'downside': round(self.downside),
            'allocation': self.allocation,
            'caution': self.caution,
        }


def _allocation_rows(equity: float, months: int) -> list[dict]:
    """Where the money actually goes, as instruments rather than asset classes."""
    debt = 1 - equity
    rows = []

    if equity > 0:
        rows.append({
            'instrument': 'Equity index fund',
            'share': round(equity * 100),
            'rate': round(RETURNS['equity'] * 100, 1),
            'why': 'The growth engine. Expect it to fall hard at least once before you need it.',
        })

    if debt > 0:
        # Under five years a fixed deposit ladder is the honest recommendation:
        # it is guaranteed, and the return difference against a debt fund does
        # not compensate for any uncertainty at that horizon.
        if months <= 60:
            rows.append({
                'instrument': 'Fixed deposit ladder',
                'share': round(debt * 100),
                'rate': round(RETURNS['fd'] * 100, 1),
                'why': 'Guaranteed, and a ladder keeps part of it reachable every year.',
            })
        else:
            rows.append({
                'instrument': 'Debt fund or PPF',
                'share': round(debt * 100),
                'rate': round(RETURNS['debt_fund'] * 100, 1),
                'why': 'Steadier than equity, and taxed better than an FD if held over three years.',
            })

    return rows


def fd_ladder(amount: float, months: int) -> list[dict]:
    """A deposit ladder sized to the horizon.

    A single long deposit has to be broken for a partial need, and breaking it
    costs a penalty on the whole amount. A ladder matures in tranches, so one
    year's money is always within reach.
    """
    years = max(1, min(5, round(months / 12)))
    per_rung = amount / years

    return [
        {
            'tenure_years': rung,
            'amount': round(per_rung),
            'matures_in_months': rung * 12,
            'value_at_maturity': round(future_value(per_rung, RETURNS['fd'], rung * 12)),
        }
        for rung in range(1, years + 1)
    ]


# --------------------------------------------------------------------------- #
# The plan                                                                     #
# --------------------------------------------------------------------------- #

def build(
    *,
    target_amount: float,
    target_date: date,
    saved: float = 0.0,
    monthly_capacity: float = 0.0,
    category_key: str = 'general',
    today: date | None = None,
) -> dict:
    """Everything the goal page needs: the target, the options, and the verdict."""
    category = category_for(category_key)
    months = months_until(target_date, today)

    # The cost then, not the cost now. Planning against today's price is the
    # commonest reason goals are underfunded.
    inflated = inflate(target_amount, category.inflation, months)

    recommended_equity = equity_share(months, category.criticality)
    plans = [
        _safe_plan(inflated, saved, months),
        _balanced_plan(inflated, saved, months, recommended_equity, category),
    ]

    growth_equity = min(0.80, recommended_equity + 0.25)
    if months >= 60 and category.criticality != 'critical' and growth_equity > recommended_equity:
        plans.append(_growth_plan(inflated, saved, months, growth_equity))

    recommended = plans[1] if len(plans) > 1 else plans[0]
    feasibility = _feasibility(recommended, monthly_capacity, months, inflated, saved)

    return {
        'category': {
            'key': category.key,
            'label': category.label,
            'icon': category.icon,
            'criticality': category.criticality,
            'note': category.note,
        },
        'months_remaining': months,
        'years_remaining': round(months / 12, 1),
        'target_today': round(target_amount),
        'target_at_date': round(inflated),
        'inflation_percent': round(category.inflation * 100, 1),
        'already_saved': round(saved),
        'recommended': recommended.key,
        'plans': [plan.as_dict() for plan in plans],
        'ladder': fd_ladder(inflated * (1 - recommended.equity), months),
        'feasibility': feasibility,
        'borrowing': _borrowing(category, inflated),
    }


def _safe_plan(target: float, saved: float, months: int) -> Plan:
    rate = RETURNS['fd'] if months <= 60 else RETURNS['ppf']
    monthly = sip_required(target, rate, months, saved)
    projected = future_value(saved, rate, months) + sip_future_value(monthly, rate, months)

    return Plan(
        key='safe',
        label='Capital protected',
        summary='Nothing is at risk of falling. You pay for that with a lower return, so the '
                'monthly amount is the highest of the three.',
        equity=0.0,
        expected_return=rate,
        monthly_required=monthly,
        projected=projected,
        # A guaranteed instrument has no market downside; the risk is that
        # inflation outruns it, which the inflated target already reflects.
        downside=projected,
        allocation=_allocation_rows(0.0, months),
    )


def _balanced_plan(target: float, saved: float, months: int, equity: float, category: Category) -> Plan:
    rate = blended_return(equity)
    monthly = sip_required(target, rate, months, saved)
    projected = future_value(saved, rate, months) + sip_future_value(monthly, rate, months)

    caution = ''
    if equity == 0:
        caution = 'At this horizon nothing belongs in equity, so this is the same as the protected plan.'
    elif category.criticality == 'critical':
        caution = ('Held down deliberately: this goal cannot be postponed, so it carries less '
                   'equity than the horizon alone would allow.')

    return Plan(
        key='balanced',
        label='Balanced',
        summary='The mix this horizon and this kind of goal can justify. Recommended unless you '
                'have a specific reason to move.',
        equity=equity,
        expected_return=rate,
        monthly_required=monthly,
        projected=projected,
        downside=projected * (1 - equity * EQUITY_DRAWDOWN),
        allocation=_allocation_rows(equity, months),
        caution=caution,
    )


def _growth_plan(target: float, saved: float, months: int, equity: float) -> Plan:
    rate = blended_return(equity)
    monthly = sip_required(target, rate, months, saved)
    projected = future_value(saved, rate, months) + sip_future_value(monthly, rate, months)

    return Plan(
        key='growth',
        label='Growth',
        summary='More equity, a lower monthly amount, and a genuinely wider range of outcomes. '
                'Only offered because this goal can slip if it has to.',
        equity=equity,
        expected_return=rate,
        monthly_required=monthly,
        projected=projected,
        downside=projected * (1 - equity * EQUITY_DRAWDOWN),
        allocation=_allocation_rows(equity, months),
        caution='If markets fall in the last two years, this plan finishes short. Move to the '
                'protected mix as the date approaches.',
    )


def _feasibility(plan: Plan, capacity: float, months: int, target: float, saved: float) -> dict:
    """Can they actually afford the recommended plan, and if not, what must move?"""
    needed = plan.monthly_required

    if capacity <= 0:
        return {
            'known': False,
            'message': 'Tell us what you can set aside each month and this becomes a real plan '
                       'rather than a number.',
        }

    if capacity >= needed:
        spare = capacity - needed
        return {
            'known': True,
            'achievable': True,
            'monthly_required': round(needed),
            'monthly_capacity': round(capacity),
            'surplus': round(spare),
            'message': f'Affordable. You need ₹{needed:,.0f} a month and can manage '
                       f'₹{capacity:,.0f}, leaving ₹{spare:,.0f} for other goals.',
        }

    # Not affordable: say which lever moves it, with the number attached.
    reachable = future_value(saved, plan.expected_return, months) + sip_future_value(
        capacity, plan.expected_return, months
    )
    extra_months = _months_needed(target, saved, capacity, plan.expected_return)

    return {
        'known': True,
        'achievable': False,
        'monthly_required': round(needed),
        'monthly_capacity': round(capacity),
        'shortfall_monthly': round(needed - capacity),
        'reachable_amount': round(reachable),
        'months_needed': extra_months,
        'message': f'At ₹{capacity:,.0f} a month you reach about ₹{reachable:,.0f} of '
                   f'₹{target:,.0f}. Either raise the monthly amount by '
                   f'₹{needed - capacity:,.0f}, push the date out to about '
                   f'{round(extra_months / 12, 1)} years, or lower the target.',
    }


def _months_needed(target: float, saved: float, monthly: float, rate: float, cap: int = 600) -> int:
    """How long ``monthly`` takes to reach the target. Capped at fifty years."""
    for months in range(1, cap + 1):
        if future_value(saved, rate, months) + sip_future_value(monthly, rate, months) >= target:
            return months
    return cap


def _borrowing(category: Category, target: float) -> dict | None:
    """For goals people normally borrow for, what the loan side actually costs."""
    if not category.borrowable:
        return None

    rates = {'home': 0.085, 'education': 0.090, 'car': 0.095, 'wedding': 0.130, 'business': 0.110}
    years = {'home': 20, 'education': 10, 'car': 5, 'wedding': 5, 'business': 5}

    rate = rates.get(category.key, 0.11)
    term = years.get(category.key, 5)

    # Half the target, as an illustration of part-funding rather than a
    # recommendation to borrow a particular amount.
    loan = emi(target * 0.5, rate, term)
    loan['note'] = (
        f'Borrowing half of this at {loan["rate_percent"]}% over {term} years costs '
        f'₹{loan["monthly"]:,.0f} a month and ₹{loan["total_interest"]:,.0f} in interest. '
        'Saving more up front is the cheapest way to reduce that number.'
    )
    return loan
