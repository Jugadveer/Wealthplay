"""
Reading a person's situation before recommending anything.

The goal form used to make the user classify their own goal from a fixed grid,
which asks them to know the answer the app is supposed to work out. This module
does the work instead: it reads what they wrote and what they earn, decides how
critical the goal is and how much risk their finances can actually absorb, and
hands that to :mod:`ai.tutor` to say out loud.

Everything here is deterministic and works with no model available. The model's
job is to phrase the read and ask the question; the judgement itself is
arithmetic, because a recommendation about somebody's money should not depend on
whether an API key is set.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .planner import BY_KEY, DEFAULT_CATEGORY, Category

# Words that place a goal, checked against what the user actually typed. Ordered
# by criticality so "my child's wedding" reads as the wedding, not the child.
KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ('emergency', ('emergency', 'rainy day', 'buffer', 'contingency', 'safety net')),
    ('retirement', ('retire', 'retirement', 'pension', 'old age', 'fire')),
    ('education', ('school', 'college', 'university', 'tuition', 'fees', 'degree',
                   'education', 'mba', 'masters', 'study', 'child')),
    ('wedding', ('wedding', 'marriage', 'shaadi', 'engagement')),
    ('home', ('home', 'house', 'flat', 'apartment', 'property', 'down payment',
              'downpayment', 'deposit', 'plot')),
    ('business', ('business', 'startup', 'shop', 'venture', 'franchise', 'capital')),
    ('car', ('car', 'bike', 'scooter', 'vehicle', 'motorcycle')),
    ('travel', ('travel', 'trip', 'holiday', 'vacation', 'europe', 'japan', 'tour')),
    ('gadget', ('phone', 'laptop', 'camera', 'console', 'watch', 'gift', 'iphone')),
)


def classify(text: str) -> Category:
    """Work out what kind of goal this is from what the user wrote."""
    lowered = f' {(text or "").lower()} '

    for key, words in KEYWORDS:
        if any(re.search(rf'\b{re.escape(word)}', lowered) for word in words):
            return BY_KEY[key]

    return DEFAULT_CATEGORY


@dataclass
class Capacity:
    """How much risk this person's finances can absorb, and why."""

    level: str  # low | moderate | high
    surplus: float
    surplus_ratio: float
    months: int
    reasons: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            'level': self.level,
            'surplus': round(self.surplus),
            'surplus_ratio': round(self.surplus_ratio * 100),
            'reasons': self.reasons,
            'blockers': self.blockers,
        }


# A goal inside three years cannot ride out a fall, whatever the income.
SHORT_HORIZON_MONTHS = 36

# Below this share of income left over, there is nothing to lose safely.
THIN_SURPLUS = 0.15
COMFORTABLE_SURPLUS = 0.30


def capacity(
    *,
    monthly_income: float,
    monthly_commitments: float,
    months: int,
    dependants: int = 0,
    has_emergency_fund: bool = False,
    criticality: str = 'important',
) -> Capacity:
    """Assess risk capacity — what they can afford to lose, not what they want to.

    Capacity and appetite are different questions. This answers the first one;
    the user answers the second, which is the whole point of asking them.
    """
    income = max(0.0, monthly_income)
    surplus = income - max(0.0, monthly_commitments)
    ratio = surplus / income if income > 0 else 0.0

    reasons: list[str] = []
    blockers: list[str] = []

    if income <= 0:
        return Capacity('low', 0.0, 0.0, months,
                        reasons=['No income figure given, so this is the cautious default.'])

    if ratio >= COMFORTABLE_SURPLUS:
        level = 'high'
        reasons.append(f'{ratio:.0%} of your income is uncommitted, which is a real buffer.')
    elif ratio >= THIN_SURPLUS:
        level = 'moderate'
        reasons.append(f'{ratio:.0%} of your income is uncommitted — enough to invest, not enough to absorb a shock.')
    else:
        level = 'low'
        blockers.append(f'Only {ratio:.0%} of your income is left after commitments.')

    if not has_emergency_fund:
        blockers.append('No emergency fund yet, so a bad month would force you to sell.')
        level = 'low' if level == 'moderate' else min_level(level, 'moderate')

    if months < SHORT_HORIZON_MONTHS:
        blockers.append(
            f'{months} months is too short to recover from a fall, whatever your income allows.'
        )
        level = 'low'

    if dependants > 0 and criticality == 'critical':
        blockers.append(
            f'{dependants} {"person depends" if dependants == 1 else "people depend"} on this, '
            'so the downside matters more than the upside.'
        )
        level = min_level(level, 'moderate')

    if months >= 120 and level != 'low':
        reasons.append('Ten years or more is long enough for equity to recover from a bad stretch.')

    return Capacity(level, surplus, ratio, months, reasons=reasons, blockers=blockers)


ORDER = {'low': 0, 'moderate': 1, 'high': 2}


def min_level(a: str, b: str) -> str:
    """The more cautious of two levels."""
    return a if ORDER[a] <= ORDER[b] else b


# What to say when no model is available. Same judgement, plainer words.
VERDICTS = {
    'high': (
        'can_take_risk',
        'Your numbers can carry some risk on this one.',
        'Do you want the plan that uses that, or would you rather stay on the safe side?',
    ),
    'moderate': (
        'be_careful',
        'You can take a measured amount of risk here, but not a lot.',
        'Take the balanced plan, or would you rather be more careful than that?',
    ),
    'low': (
        'stay_safe',
        'This one should stay safe.',
        'The protected plan costs more each month. Can you make that work?',
    ),
}


def fallback_verdict(cap: Capacity, category: Category) -> dict:
    """The assessment stated without a model, so the feature never simply fails."""
    stance, headline, question = VERDICTS[cap.level]

    return {
        'available': False,
        'criticality': category.criticality,
        'category': category.key,
        'stance': stance,
        'headline': headline,
        'reasoning': cap.blockers + cap.reasons,
        'question': question,
    }
