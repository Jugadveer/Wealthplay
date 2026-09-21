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

from ai import tutor

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


def narrative_review(portfolio_data: dict) -> dict:
    """Model-written portfolio review.

    ``available: False`` when no provider answered. The UI hides the block
    rather than showing something written by a template.
    """
    holdings = portfolio_data.get('holdings') or []
    if not holdings:
        return {'available': False}

    review = tutor.review_portfolio(
        holdings,
        cash=portfolio_data.get('balance', 0),
        pnl_percent=portfolio_data.get('total_pnl_percent', 0),
    )
    if not review:
        return {'available': False}

    risks = review.get('risks')
    return {
        'available': True,
        'headline': review.get('headline', ''),
        'risks': risks if isinstance(risks, list) else [str(risks)],
        'next_step': review.get('next_step', ''),
        'concentration_grade': review.get('concentration_grade', ''),
    }
