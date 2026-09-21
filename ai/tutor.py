"""
Every AI feature in the product, as one function each.

Each function owns its prompt, decides whether the answer is cacheable, and
returns a plain dict or string. Views stay thin and there is exactly one place
to read to know what the model is being asked.

All of them degrade honestly: if no provider answers, the caller gets ``None``
or an ``available: False`` payload and the UI says so. Nothing here fabricates
an analysis and labels it AI -- the previous build shipped hardcoded strings
under an "AI" heading, including one that read "the volume volume surge".
"""

from __future__ import annotations

from datetime import date

import logging

from . import client

logger = logging.getLogger(__name__)

TUTOR_VOICE = (
    "You are Nex, a financial literacy tutor for beginners in India. "
    "Explain plainly, use rupees, and prefer a concrete number over an adjective. "
    "Never recommend a specific real-world investment or predict a price. "
    "No preamble, no sign-off, no markdown headings."
)

ANALYST_VOICE = (
    "You are a markets educator reviewing a beginner's practice portfolio. "
    "This is a simulation with virtual money, so be direct about mistakes. "
    "Teach the reasoning, never give real-world financial advice."
)


def _safe(fn, *args, **kwargs):
    """Run an AI call, returning ``None`` instead of raising into a view."""
    try:
        return fn(*args, **kwargs)
    except (client.NoProviderAvailable, ValueError) as exc:
        logger.warning('%s unavailable: %s', getattr(fn, '__name__', fn), exc)
        return None


# --------------------------------------------------------------------------- #
# Lesson mentor                                                                #
# --------------------------------------------------------------------------- #

def answer_lesson_question(question: str, *, module_title: str, theory: str, history=None) -> str | None:
    """Answer a learner's question grounded in the module they are reading.

    ``history`` is the recent turns as ``[(role, text), ...]`` so follow-ups
    like "why?" resolve against what was just said.
    """
    transcript = ''
    for role, text in (history or [])[-6:]:
        speaker = 'Learner' if role == 'user' else 'Nex'
        transcript += f'{speaker}: {text}\n'

    prompt = (
        f'Module: {module_title}\n'
        f'What the module teaches:\n"""{theory[:1800]}"""\n\n'
        f'{transcript}'
        f'Learner: {question}\n\n'
        'Answer in 2-4 sentences. Stay on this module unless the learner clearly '
        'asks about something else. If the module does not cover it, say so and '
        'answer briefly anyway.'
    )
    # Not cached: answers depend on the conversation so far.
    return _safe(client.complete, prompt, system=TUTOR_VOICE, max_tokens=320)


def explain_wrong_answer(question: str, chosen: str, correct: str, *, module_title: str) -> str | None:
    """Explain why a quiz answer was wrong.

    Cached on the question/answer pair: the explanation for choosing option B on
    a given question is the same for everyone.
    """
    prompt = (
        f'Module: {module_title}\n'
        f'Question: {question}\n'
        f'The learner chose: {chosen}\n'
        f'The correct answer: {correct}\n\n'
        'In 2-3 sentences, name the specific misunderstanding behind their choice, '
        'then give the rule that resolves it. Do not restate the correct answer verbatim.'
    )
    return _safe(
        client.complete,
        prompt,
        system=TUTOR_VOICE,
        max_tokens=220,
        cache_key=f'wrong:{module_title}:{question}:{chosen}',
    )


# --------------------------------------------------------------------------- #
# Markets                                                                      #
# --------------------------------------------------------------------------- #

def chart_hint(symbol: str, name: str, series: list[dict]) -> str | None:
    """A teaching hint for the prediction game, derived from the actual series.

    The numbers are computed here rather than asked for, so the model describes
    real price action instead of inventing it.
    """
    closes = [float(p['close']) for p in series if p.get('close')]
    if len(closes) < 10:
        return None

    recent, earlier = closes[-10:], closes[-30:-10] or closes[:10]
    momentum = (recent[-1] / recent[0] - 1) * 100
    versus_mean = (recent[-1] / (sum(earlier) / len(earlier)) - 1) * 100
    swing = (max(recent) - min(recent)) / recent[-1] * 100

    prompt = (
        f'{name} ({symbol}) over the last 10 sessions:\n'
        f'- moved {momentum:+.1f}%\n'
        f'- sits {versus_mean:+.1f}% against its prior 20-session average\n'
        f'- traded in a {swing:.1f}% range\n\n'
        'In one sentence, tell a beginner which of these signals matters most '
        'here and what it suggests to watch. Do not state a direction or a target.'
    )
    return _safe(
        client.complete,
        prompt,
        system=TUTOR_VOICE,
        max_tokens=120,
        # Bucketed so the hint is stable for a session but refreshes as prices move.
        cache_key=f'hint:{symbol}:{round(momentum, 1)}',
    )


def judge_prediction(symbol: str, *, called: str, actual: str, rationale: str, move_percent: float) -> str | None:
    """Grade a prediction on its reasoning, not only its outcome.

    The point of the game is process: a good call for a bad reason should not
    read as a win.
    """
    prompt = (
        f'A learner predicted {symbol} would be {called}. It actually moved '
        f'{move_percent:+.2f}% ({actual}).\n'
        f'Their reasoning: "{rationale or "(none given)"}"\n\n'
        'In 2-3 sentences: say whether the reasoning was sound independently of '
        'the outcome, name one thing they missed, and give one habit to carry '
        'into the next call.'
    )
    return _safe(client.complete, prompt, system=ANALYST_VOICE, max_tokens=220)


def review_portfolio(holdings: list[dict], *, cash: float, pnl_percent: float) -> dict | None:
    """Structured risk review of a practice portfolio."""
    if not holdings:
        return None

    lines = '\n'.join(
        f'- {h["symbol"]} ({h.get("sector", "Unknown")}): {h["quantity"]:g} shares, '
        f'{h["pnl_percent"]:+.1f}%, {h["current_value"] / max(sum(x["current_value"] for x in holdings), 1) * 100:.0f}% of holdings'
        for h in holdings[:12]
    )

    prompt = (
        f'Practice portfolio, virtual money:\n{lines}\n'
        f'Uninvested cash: Rs {cash:,.0f}\n'
        # Whole percent, not two decimals: the review is about the shape of the
        # portfolio, and quoting a figure that moves with every tick would make
        # an otherwise identical prompt unique on every page load.
        f'Overall return: {pnl_percent:+.0f}%\n\n'
        'Return JSON with:\n'
        '  headline: one sentence naming the single biggest issue\n'
        '  risks: 2-3 specific observations, each citing a holding or a number\n'
        '  next_step: one concrete action to take in this simulator\n'
        '  concentration_grade: one of A, B, C, D'
    )

    composition = ','.join(sorted(f'{h["symbol"]}:{h["quantity"]:g}' for h in holdings))

    return _safe(
        client.complete_json,
        prompt,
        system=ANALYST_VOICE,
        schema_hint='headline, risks, next_step, concentration_grade',
        max_tokens=450,
        # Cached on composition rather than on exact value: rebuying the same
        # names should not cost a second of model time, but changing what you
        # hold should.
        cache_key=f'portfolio-review:{composition}',
    )


def critique_trade(symbol: str, *, action: str, quantity: int, rationale: str, weight_percent: float) -> str | None:
    """React to the reason a learner gave for a trade, at the moment they place it."""
    prompt = (
        f'A learner is about to {action} {quantity} shares of {symbol}. '
        f'This position would be {weight_percent:.0f}% of their portfolio.\n'
        f'Their stated reason: "{rationale}"\n\n'
        'In 2 sentences: name one thing their reasoning handles well and one '
        'question they have not answered. Do not tell them whether to trade.'
    )
    return _safe(client.complete, prompt, system=ANALYST_VOICE, max_tokens=180)


# --------------------------------------------------------------------------- #
# Progress                                                                     #
# --------------------------------------------------------------------------- #

def weekly_recap(stats: dict) -> str | None:
    """Narrate the week from the user's own numbers."""
    prompt = (
        'A learner\'s week in a finance learning app:\n'
        f'- modules completed: {stats.get("modules", 0)}\n'
        f'- quiz accuracy: {stats.get("accuracy", 0):.0f}%\n'
        f'- daily puzzles solved: {stats.get("puzzles", 0)} of {stats.get("puzzle_days", 7)}\n'
        f'- current streak: {stats.get("streak", 0)} days\n'
        f'- practice portfolio return: {stats.get("portfolio_return", 0):+.1f}%\n'
        f'- weakest topic: {stats.get("weak_topic", "not enough data")}\n\n'
        'Write 3 sentences: what actually improved, the one number worth '
        'attention, and what to do next week. Address them as "you". No praise '
        'that the numbers do not support.'
    )

    # Keyed on the figures themselves, and on the day. A recap is the same recap
    # until one of the numbers changes; without this it regenerated on every
    # visit to Progress and cost three seconds each time.
    fingerprint = ':'.join(
        f'{key}={stats.get(key)}'
        for key in ('modules', 'accuracy', 'puzzles', 'streak', 'portfolio_return', 'weak_topic')
    )

    return _safe(
        client.complete,
        prompt,
        system=TUTOR_VOICE,
        max_tokens=220,
        cache_key=f'recap:{date.today()}:{fingerprint}',
    )


def generate_drill_questions(module_title: str, theory: str, count: int = 3) -> list[dict] | None:
    """Generate practice questions from module theory.

    This is what keeps the daily drill from running dry: the hand-authored bank
    is ~96 questions, which one committed user exhausts in a weekend.
    Cached per module, so each module is generated once and reused.
    """
    prompt = (
        f'Module: {module_title}\n'
        f'Content:\n"""{theory[:2000]}"""\n\n'
        f'Write {count} multiple-choice questions testing whether someone can '
        'apply this, not whether they memorised it. Each needs 4 options where '
        'the wrong ones are plausible mistakes, not obvious filler.\n'
        'Return JSON: {"questions": [{"question": str, "options": [str x4], '
        '"correct_index": int, "explanation": str}]}'
    )
    payload = _safe(
        client.complete_json,
        prompt,
        system=TUTOR_VOICE,
        schema_hint='questions',
        max_tokens=1400,
        heavy=True,
        cache_key=f'drill:{module_title}:{count}',
    )
    if not payload:
        return None

    # Drop anything malformed rather than rendering a broken question.
    return [
        q
        for q in payload.get('questions', [])
        if isinstance(q.get('options'), list)
        and len(q['options']) == 4
        and isinstance(q.get('correct_index'), int)
        and 0 <= q['correct_index'] < 4
    ]
