"""
Analysis layered on top of a valued portfolio.

Two kinds of output live here and they are labelled differently in the UI:

* **Computed** -- concentration, ESG weighting, sell-discipline scoring. These
  are deterministic formulas over the user's own numbers. They always work.
* **Model-written** -- the narrative review. This one can be unavailable, and
  the payload says so rather than substituting a template.

Keeping them apart is the point. The old build blended both under an "AI
Recommendations" heading, so a hardcoded sentence was indistinguishable from a
generated one.
"""

from __future__ import annotations

from . import pricing


def _clamp(value, low, high):
    return max(low, min(high, value))


# --------------------------------------------------------------------------- #
# Concentration                                                                #
# --------------------------------------------------------------------------- #

def sector_weights(holdings: list[dict]) -> dict[str, float]:
    """Portfolio value by sector."""
    weights: dict[str, float] = {}
    for holding in holdings:
        sector = holding.get('sector') or 'Unknown'
        weights[sector] = weights.get(sector, 0.0) + float(holding.get('current_value') or 0)
    return weights


def concentration(holdings: list[dict]) -> dict:
    """Diversification measured with a Herfindahl index, rescaled so higher is better.

    A single-holding portfolio scores 0; an evenly spread one approaches 100.
    """
    weights = sector_weights(holdings)
    total = sum(weights.values())

    if total <= 0:
        return {'score': 0, 'top_sector': None, 'top_weight_percent': 0.0, 'sectors': {}}

    shares = {sector: value / total for sector, value in weights.items()}
    top_sector, top_share = max(shares.items(), key=lambda kv: kv[1])
    hhi = sum(share**2 for share in shares.values())

    return {
        'score': int(_clamp(round((1 - hhi) * 100), 0, 100)),
        'top_sector': top_sector,
        'top_weight_percent': round(top_share * 100, 1),
        'sectors': {sector: round(share * 100, 1) for sector, share in shares.items()},
    }


def esg_summary(holdings: list[dict]) -> dict:
    """Value-weighted ESG and carbon profile across holdings."""
    total = sum(float(h.get('current_value') or 0) for h in holdings)
    if total <= 0:
        return {
            'available': False,
            'note': 'Buy something first — ESG is weighted by position size.',
        }

    esg = carbon = 0.0
    by_sector = {}

    for holding in holdings:
        weight = float(holding.get('current_value') or 0) / total
        profile = pricing.sector_profile(holding.get('sector'))
        esg += weight * profile['esg_score']
        carbon += weight * profile['carbon_intensity']
        by_sector[holding.get('sector') or 'Unknown'] = profile

    cleanest = max(by_sector.items(), key=lambda kv: kv[1]['esg_score'])[0]
    dirtiest = max(by_sector.items(), key=lambda kv: kv[1]['carbon_intensity'])[0]

    return {
        'available': True,
        'esg_score': round(esg, 1),
        'carbon_intensity': round(carbon, 1),
        'cleanest_sector': cleanest,
        'highest_carbon_sector': dirtiest,
        'note': (
            f'Your carbon intensity is {carbon:.0f}, driven mostly by {dirtiest}. '
            f'Sector profiles here are illustrative, not a rating agency score.'
        ),
    }


# --------------------------------------------------------------------------- #
# Sell discipline                                                              #
# --------------------------------------------------------------------------- #

def sell_discipline(symbol: str, *, sold: float, held_before: float, price: float, avg_price: float) -> dict:
    """Score a sell for process rather than outcome.

    Beginners tend to sell winners early and losers late. The score is an
    explainable heuristic over recent price action, and every adjustment is
    returned in ``reasons`` so the learner can see what drove it.
    """
    series = pricing.history(symbol, days=30)
    closes = [p['close'] for p in series] or [price]

    sold_share = (sold / held_before) if held_before > 0 else 1.0
    pnl_percent = ((price - avg_price) / avg_price * 100) if avg_price > 0 else 0.0
    recent_high = max(closes)
    off_high = ((price - recent_high) / recent_high * 100) if recent_high > 0 else 0.0
    ma20 = sum(closes[-20:]) / len(closes[-20:])

    score = 50
    reasons = []

    if pnl_percent >= 5:
        score += 18
        reasons.append('Sold in profit, which usually means the exit was planned.')
    elif pnl_percent <= -8:
        score -= 18
        reasons.append(f'Sold at {pnl_percent:.0f}%, which is often an emotional exit.')

    if off_high <= -10 and sold_share > 0.5:
        score -= 15
        reasons.append(f'Large exit while {abs(off_high):.0f}% below the recent high.')

    if price < ma20 and sold_share <= 0.35:
        score += 10
        reasons.append('Trimmed a small slice below trend — that is risk control.')

    if sold_share < 0.2:
        score += 8
        reasons.append('Partial sale keeps the position alive if the thesis holds.')
    elif sold_share > 0.8:
        score -= 8
        reasons.append('Near-total exit leaves no room to be partly right.')

    score = int(_clamp(round(score), 0, 100))

    if score >= 70:
        behaviour, verdict = 'disciplined', 'This looks process-led. Write down the rule you followed so you can repeat it.'
    elif score >= 40:
        behaviour, verdict = 'mixed', 'Parts of this were tactical. Check whether it matched your plan before the trade.'
    else:
        behaviour, verdict = 'reactive', 'This reads as fear-driven. Next time, re-check the thesis before selling.'

    return {
        'score': score,
        'behaviour': behaviour,
        'verdict': verdict,
        'sold_share': round(sold_share, 2),
        'pnl_percent_at_sale': round(pnl_percent, 2),
        'off_recent_high_percent': round(off_high, 2),
        'reasons': reasons or ['Not enough price history for a confident read.'],
    }


# --------------------------------------------------------------------------- #
# Coaching                                                                     #
# --------------------------------------------------------------------------- #

def diversification_nudge(holdings: list[dict]) -> dict:
    """A concentration prompt, computed not generated."""
    if not holdings:
        return {
            'available': False,
            'message': 'Open a position to start getting portfolio feedback.',
        }

    stats = concentration(holdings)
    weight = stats['top_weight_percent']
    sector = stats['top_sector']

    if weight >= 55:
        severity = 'high'
        message = f'{weight:.0f}% of your holdings sit in {sector}. One sector shock moves your whole portfolio.'
    elif weight >= 40:
        severity = 'moderate'
        message = f'{sector} is your largest sector at {weight:.0f}%. Worth watching, not urgent.'
    else:
        severity = 'low'
        message = f'Spread looks reasonable — {sector} leads at {weight:.0f}%.'

    return {
        'available': True,
        'severity': severity,
        'message': message,
        'top_sector': sector,
        'top_weight_percent': weight,
        'diversification_score': stats['score'],
    }


def concentration_grade(score: int) -> str:
    """A letter for the diversification score.

    Computed, never asked for. Given a portfolio with 90% of its value in one
    stock and asked to grade the concentration, the local model returns "A" —
    the best grade for the worst case. The thresholds below are arbitrary in the
    way any grading scale is, but they are at least monotonic.
    """
    if score >= 75:
        return 'A'
    if score >= 55:
        return 'B'
    if score >= 30:
        return 'C'
    return 'D'




def narrative_review(portfolio_data: dict) -> dict:
    """The portfolio review: what is concentrated, what is losing, what to do.

    Computed, not generated, and this one was measured before it was decided.
    Handed a portfolio that is 81% IT, graded C, with every figure in the
    prompt, the local model replied:

        headline:  "The portfolio is well-diversified and has a return of +6%"
        risk:      "Banking holdings have a negative return (-4.2%)"
        next step: "Invest in more IT stocks"

    The portfolio is not well diversified, -4.2% is INFY and INFY is IT, and
    buying more IT is the thing that caused the concentration being reported.
    A model that cannot attach a number to the right holding cannot be trusted
    to phrase a risk either, because a risk *is* an attribution.

    So the analysis is arithmetic. It is right every time, it costs nothing, and
    it says the same thing twice for the same portfolio — which the model did
    not. ``available`` stays in the payload so the UI contract is unchanged.
    """
    holdings = portfolio_data.get('holdings') or []
    if not holdings:
        return {'available': False}

    stats = concentration(holdings)
    grade = concentration_grade(stats['score'])
    total = sum(float(h.get('current_value') or 0) for h in holdings)
    cash = float(portfolio_data.get('balance') or 0)
    pnl_percent = float(portfolio_data.get('total_pnl_percent') or 0)

    sector = stats['top_sector'] or 'one sector'
    weight = stats['top_weight_percent']

    return {
        'available': True,
        'headline': _headline(grade, sector, weight, len(holdings)),
        'risks': _risks(holdings, total=total, cash=cash, sector=sector, weight=weight),
        'next_step': _next_step(grade, sector, len(holdings), cash, total),
        'concentration_grade': grade,
        'diversification_score': stats['score'],
        'total_pnl_percent': round(pnl_percent, 2),
    }


def _headline(grade: str, sector: str, weight: float, count: int) -> str:
    """The single most important thing about the shape of this portfolio."""
    if grade == 'D':
        return f'Almost everything you own rides on {sector}, at {weight:.0f}% of your holdings.'
    if grade == 'C':
        return f'{sector} is {weight:.0f}% of your holdings, which is more than one sector should decide.'
    if grade == 'B':
        return f'Reasonably spread, with {sector} the largest at {weight:.0f}%.'
    return f'Well spread across {count} holdings, {sector} largest at {weight:.0f}%.'


def _risks(holdings: list[dict], *, total: float, cash: float, sector: str, weight: float) -> list[str]:
    """Specific observations, each tied to a holding or a figure that exists."""
    risks = []

    if weight >= 40:
        risks.append(
            f'A shock to {sector} moves {weight:.0f}% of your holdings at once. '
            'That is one decision, not a portfolio.'
        )

    largest = max(holdings, key=lambda h: float(h.get('current_value') or 0))
    largest_weight = float(largest.get('current_value') or 0) / total * 100 if total else 0
    if largest_weight >= 35:
        risks.append(
            f'{largest["symbol"]} alone is {largest_weight:.0f}% of your holdings. '
            'A single company should not be able to decide your year.'
        )

    worst = min(holdings, key=lambda h: float(h.get('pnl_percent') or 0))
    worst_pnl = float(worst.get('pnl_percent') or 0)
    if worst_pnl <= -10:
        risks.append(
            f'{worst["symbol"]} is down {abs(worst_pnl):.1f}%. Check whether the reason you '
            'bought it still holds, rather than waiting to get back to even.'
        )

    invested_share = total / (total + cash) * 100 if (total + cash) else 0
    if invested_share < 40 and cash > 0:
        risks.append(
            f'Only {invested_share:.0f}% of the account is invested. Cash is a position too, '
            'and right now it is your largest one.'
        )

    if len(holdings) < 3:
        risks.append(
            f'With {len(holdings)} holding{"s" if len(holdings) != 1 else ""}, luck and skill '
            'look identical. You cannot read your own track record yet.'
        )

    # Never empty: a portfolio with no flags has earned being told so.
    return risks[:3] or [
        'Nothing here stands out as a concentration risk. Keep the position sizes '
        'where they are as you add to it.'
    ]


def _next_step(grade: str, sector: str, count: int, cash: float, total: float) -> str:
    """One action, in this simulator, that addresses the biggest issue found."""
    if grade in {'C', 'D'}:
        return (
            f'Add a position outside {sector} rather than more inside it. Spreading across '
            'sectors does more for your risk than picking a better name in the one you hold.'
        )
    if count < 4:
        return 'Add a third or fourth sector so no single one can carry the whole result.'
    if cash > total:
        return 'Put some of the idle cash to work, or decide deliberately that you are waiting.'
    return (
        'Record why you hold each position. The review grades your reasoning, and it needs '
        'something written down before the outcome is known.'
    )
