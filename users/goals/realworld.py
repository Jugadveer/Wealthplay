"""
Turning an allocation into instructions someone could actually carry out.

The planner answers "45% equity, ₹14,318 a month". That is correct and useless
on its own — nobody can go and buy 45% equity. This module turns it into
sleeves with rupee amounts, named instrument types, deposit tenures at real
rates, and a review cadence, so the output is a list of actions rather than a
pie chart.

Live quotes come through :mod:`market_data.services`, which is the only module
allowed to call a provider. They are used for context — what the index actually
holds and at what price today — not to pick anything.

**This is educational.** It names categories of instrument and shows real
listings as examples of what a broad index contains. It is not personalised
investment advice, and ``DISCLAIMER`` travels with every response so the UI
cannot render the plan without it.
"""

from __future__ import annotations

import logging

from market_data import services

from .planner import RETURNS, fd_ladder

logger = logging.getLogger(__name__)

DISCLAIMER = (
    'Educational only. These are categories of instrument and real listings shown as examples of '
    'what a broad index holds — not a recommendation to buy any particular security. Check current '
    'rates and your own tax position before acting.'
)

# The large Indian listings the app already tracks. Shown as "this is what an
# index fund holds", which is the honest reason to name them at all.
INDEX_SAMPLE = ('RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'ITC')

# Gold earns its place as ballast, not as an engine. Skipped for short horizons
# and for the emergency fund, which must not fall at all.
GOLD_SHARE = 0.08
GOLD_MIN_MONTHS = 36


def build(*, monthly: float, equity_share: float, months: int, category_key: str,
          has_emergency_fund: bool = True, lump_sum: float = 0.0) -> dict:
    """The monthly amount, split into things a person can go and do."""
    sleeves: list[dict] = []
    remaining = max(0.0, monthly)

    # Nothing else happens until there is a buffer. Investing while one bad month
    # would force a sale is the most common way a plan ends early.
    if not has_emergency_fund and category_key != 'emergency':
        buffer_amount = round(remaining * 0.25)
        remaining -= buffer_amount
        sleeves.append({
            'key': 'buffer',
            'name': 'Build the emergency buffer first',
            'monthly': buffer_amount,
            'share': 25,
            'why': 'Until six months of expenses are reachable the same day, every other plan is '
                   'one bad month from being sold at the wrong time.',
            'instruments': [{
                'type': 'Sweep-in savings or liquid fund',
                'detail': 'Same-day access. Return is not the point here.',
                'rate': round(RETURNS['savings'] * 100, 1),
            }],
        })

    gold_share = GOLD_SHARE if months >= GOLD_MIN_MONTHS and category_key != 'emergency' else 0.0
    equity_amount = round(remaining * equity_share * (1 - gold_share))
    gold_amount = round(remaining * gold_share) if gold_share else 0
    debt_amount = round(remaining - equity_amount - gold_amount)

    if equity_amount > 0:
        sleeves.append(_equity_sleeve(equity_amount, months, monthly))
    if debt_amount > 0:
        sleeves.append(_debt_sleeve(debt_amount, months, monthly, lump_sum))
    if gold_amount > 0:
        sleeves.append(_gold_sleeve(gold_amount, monthly))

    return {
        'monthly_total': round(monthly),
        'sleeves': sleeves,
        'cadence': _cadence(equity_amount > 0, months),
        'disclaimer': DISCLAIMER,
    }


def _share(amount: float, total: float) -> int:
    return round(amount / total * 100) if total else 0


def _equity_sleeve(amount: float, months: int, total: float) -> dict:
    """The growth engine, with live context on what the index actually is."""
    splits = [{
        'type': 'Nifty 50 index fund — direct plan',
        'detail': 'The cheapest way to own the market. Direct plans cost about 0.2% a year against '
                  '1.8% for an active fund; on twenty years that gap is roughly a third of the corpus.',
        'monthly': round(amount * (0.7 if months >= 84 else 1.0)),
        'rate': round(RETURNS['equity'] * 100, 1),
    }]

    # A mid-cap slice only makes sense when there is time to sit through it.
    if months >= 84:
        splits.append({
            'type': 'Nifty Midcap 150 index fund',
            'detail': 'Higher long-run return, much deeper falls. Only worth holding because you '
                      'have seven years or more before you need this money.',
            'monthly': round(amount * 0.3),
            'rate': round((RETURNS['equity'] + 0.02) * 100, 1),
        })

    return {
        'key': 'equity',
        'name': 'Equity SIP',
        'monthly': round(amount),
        'share': _share(amount, total),
        'why': 'The part that outgrows inflation. Expect it to fall 30% or more at least once '
               'before you need the money; that is the price of the return, not a malfunction.',
        'instruments': splits,
        'holds': _index_snapshot(),
        'action': 'Set up a monthly SIP with a date two days after payday, so it debits before the '
                  'money can be spent.',
    }


def _index_snapshot() -> list[dict]:
    """What a Nifty index fund is actually holding, priced now.

    Shown so the equity sleeve is a concrete thing rather than an abstraction:
    buying the index means owning these businesses at these prices today.
    """
    rows = []
    for symbol in INDEX_SAMPLE:
        try:
            quote = services.get_quote(symbol)
        except Exception:
            logger.warning('no quote for %s while building a plan', symbol, exc_info=True)
            continue

        if quote.price > 0:
            rows.append({
                'symbol': quote.symbol,
                'name': quote.name,
                'price': round(quote.price, 2),
                'change_percent': round(quote.change_percent, 2),
                'sector': quote.sector,
            })

    return rows


def _debt_sleeve(amount: float, months: int, total: float, lump_sum: float) -> dict:
    """Deposits under five years, PPF or a debt fund beyond."""
    if months <= 60:
        instruments = [{
            'type': 'Fixed deposit ladder',
            'detail': 'One deposit maturing each year rather than a single long one, so a partial '
                      'need never forces you to break the whole amount and lose the interest.',
            'monthly': round(amount),
            'rate': round(RETURNS['fd'] * 100, 1),
        }]
        ladder = fd_ladder(lump_sum, months) if lump_sum > 0 else []
    else:
        instruments = [
            {
                'type': 'PPF',
                'detail': 'Tax-free at 7.1%, and the ₹1.5 lakh a year counts towards 80C. Locked '
                          'for fifteen years, which suits a goal this far out.',
                'monthly': round(amount * 0.5),
                'rate': round(RETURNS['ppf'] * 100, 1),
            },
            {
                'type': 'Short-duration debt fund',
                'detail': 'Taxed better than an FD if held over three years, and you can withdraw '
                          'without breaking anything.',
                'monthly': round(amount * 0.5),
                'rate': round(RETURNS['debt_fund'] * 100, 1),
            },
        ]
        ladder = []

    return {
        'key': 'debt',
        'name': 'Guaranteed and near-guaranteed',
        'monthly': round(amount),
        'share': _share(amount, total),
        'why': 'The part that will still be there whatever equity does. It is what lets you leave '
               'the equity sleeve alone during a fall.',
        'instruments': instruments,
        'ladder': ladder,
        'action': 'Open the deposits in separate tranches rather than one, and set them to renew '
                  'rather than credit to your account.',
    }


def _gold_sleeve(amount: float, total: float) -> dict:
    return {
        'key': 'gold',
        'name': 'Gold',
        'monthly': round(amount),
        'share': _share(amount, total),
        'why': 'Ballast. It often rises when equity falls, and a small holding reduces how much '
               'the whole plan moves — but it produces no income, so it cannot be the engine.',
        'instruments': [
            {
                'type': 'Sovereign gold bonds',
                'detail': 'Pays 2.5% a year on top of the gold price, with no making charge, no '
                          'storage and no purity dispute. Tax-free on maturity if held to term.',
                'monthly': round(amount * 0.6),
                'rate': round((RETURNS['gold'] + 0.025) * 100, 1),
            },
            {
                'type': 'Gold ETF',
                'detail': 'Buy any month, sell any day. Use this when a bond issue is not open.',
                'monthly': round(amount * 0.4),
                'rate': round(RETURNS['gold'] * 100, 1),
            },
        ],
        'action': 'Never buy jewellery for this. Making charges run about 12% and are gone the '
                  'moment you leave the shop.',
    }


def _cadence(has_equity: bool, months: int) -> list[dict]:
    """When to do what — and, mostly, when to do nothing."""
    cadence = [
        {
            'period': 'Weekly',
            'action': 'Nothing.',
            'detail': 'Checking weekly raises the number of times you see a loss, and every one of '
                      'those is a chance to abandon the plan. There is no weekly decision here.',
        },
        {
            'period': 'Monthly',
            'action': 'Confirm the SIP and deposits went through.',
            'detail': 'A failed auto-debit costs a fee and a mark on your credit report. Two '
                      'minutes, not a review.',
        },
        {
            'period': 'Quarterly',
            'action': 'Check the split against target.',
            'detail': 'If any sleeve has drifted more than five percentage points from its target, '
                      'move the next month or two of contributions to the one that lagged rather '
                      'than selling anything.',
        },
        {
            'period': 'Yearly',
            'action': 'Raise the monthly amount with your income, and rebalance properly.',
            'detail': 'Increasing the SIP by your raise each year is the single most effective '
                      'habit available. Also harvest long-term gains up to the ₹1,25,000 exemption '
                      'and reset your cost basis at no tax cost.',
        },
    ]

    if has_equity and months > 36:
        cadence.append({
            'period': f'From about {max(2, round(months / 12) - 3)} years in',
            'action': 'Start moving equity into deposits.',
            'detail': 'Shift roughly a third of the equity sleeve to guaranteed instruments in each '
                      'of the last three years. A 30% fall in the final year is the one outcome '
                      'this plan cannot absorb.',
        })

    return cadence
