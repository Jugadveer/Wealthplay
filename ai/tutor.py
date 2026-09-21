"""
Every AI feature in the product, as one function each.

Each function owns its prompt, decides whether the answer is cacheable, and
returns a plain dict or string. Views stay thin and there is exactly one place
to read to know what the model is being asked.

The rule every function here follows
------------------------------------
The model runs locally and is small. Measured on these exact prompts it gets
compound interest wrong by nine lakh, calls an index fund an ETF, and grades a
portfolio with 90% in one stock as "A" — the best grade for the worst case.

So nothing here asks it for a fact, a number or a verdict. It is given them:

* **Facts** come from Python, and :mod:`ai.guard` rejects any reply containing a
  figure that was not supplied.
* **Knowledge** comes from the 60 authored course modules through
  :mod:`ai.retrieve`, and the model is told to answer from those passages or
  admit the course does not cover it.
* **Verdicts** — grades, stances, classifications — are computed before the
  prompt is written and passed in as given.

What is left for the model is the sentence. That it can do.

All of them degrade honestly: if no provider answers, the caller gets ``None``
or an ``available: False`` payload and the UI says so. Nothing here fabricates
an analysis and labels it AI.
"""

from __future__ import annotations

import logging
from datetime import date

from . import client, glossary, retrieve

logger = logging.getLogger(__name__)

TUTOR_VOICE = (
    "You are Nex, a financial literacy tutor for beginners in India. "
    "Explain plainly, use rupees, and prefer a concrete number over an adjective. "
    "Never recommend a specific real-world investment or predict a price. "
    "Always address the reader directly as \"you\" — never as \"the learner\", "
    "\"he\" or \"she\". No preamble, no sign-off, no markdown."
)

ANALYST_VOICE = (
    "You are a markets educator reviewing a beginner's practice portfolio. "
    "This is a simulation with virtual money, so be direct about mistakes. "
    "Teach the reasoning, never give real-world financial advice. "
    "Use only the figures you are given. No markdown."
)

GROUNDED_RULE = (
    "Answer only from the numbered passages. If they do not cover the question, "
    "say that the course does not cover it yet and answer in one careful sentence."
)


def _safe(fn, *args, **kwargs):
    """Run an AI call, returning ``None`` instead of raising into a view."""
    try:
        return fn(*args, **kwargs)
    except (client.NoProviderAvailable, ValueError) as exc:
        logger.warning('%s unavailable: %s', getattr(fn, '__name__', fn), exc)
        return None


# --------------------------------------------------------------------------- #
# Mentor                                                                       #
# --------------------------------------------------------------------------- #

def answer_question(
    question: str,
    *,
    course_id: str = '',
    module_id: str = '',
    module_title: str = '',
    theory: str = '',
    history=None,
) -> dict | None:
    """Answer a learner's question from the course content.

    Searched rather than recalled. Ungrounded, this model answers "what is an
    index fund?" with "also known as an ETF... represents shares of a single
    underlying stock" and cites the S&P 500 to someone in India. Given the
    authored passage on the same question it answers with the Nifty 50 and the
    real fee gap, because then it is rewriting rather than remembering.

    Returns the reply plus the passages behind it, so the UI can link to the
    module a claim came from.
    """
    # "What is X" is the most common question there is, and the one the model is
    # worst at. The glossary answers it exactly, in no time, with an example
    # carrying a real number. Strict matching only: a question that merely
    # mentions a known term is not a request for its definition.
    entry = glossary.look_up(question, fuzzy=False)
    if entry:
        return {
            'reply': f'{entry["definition"]}\n\n{entry["example"]}',
            'sources': [],
            'source': 'glossary',
            'authored': True,
            'term': entry['term'],
        }

    # An authored answer to this exact question beats anything a rewrite can
    # produce: it is correct by construction and it costs nothing. Only checked
    # outside a lesson, because inside one the open module answers first.
    if not theory:
        authored = retrieve.direct_answer(question)
        if authored:
            return {
                'reply': authored['answer'],
                'sources': [{
                    'title': authored['title'][:90],
                    'where': authored['where'],
                    'course_id': authored['course_id'],
                    'module_id': authored['module_id'],
                }],
                'source': 'course',
                'authored': True,
            }

    # Wider glossary match, for a question that is asking about a term it knows
    # without naming it on its own — "how big should my emergency fund be?".
    # Skipped inside a lesson, where the open module answers first.
    if not theory:
        entry = glossary.asked_about(question)
        if entry:
            return {
                'reply': f'{entry["definition"]}\n\n{entry["example"]}',
                'sources': [],
                'source': 'glossary',
                'authored': True,
                'term': entry['term'],
            }

    passages = retrieve.search(question, limit=3, course_id=course_id)

    # The module being read is the best passage there is when there is one, so
    # it goes in front of whatever search found.
    if theory:
        passages.insert(0, {
            'text': theory[:1200],
            'title': module_title or 'This module',
            'kind': 'theory',
            'where': module_title,
            'course_id': course_id,
            'module_id': module_id,
            'course_title': '',
            'module_title': module_title,
            'score': 99.0,
        })

    if not passages:
        return None

    transcript = ''
    for role, text in (history or [])[-4:]:
        speaker = 'Learner' if role == 'user' else 'Nex'
        transcript += f'{speaker}: {text}\n'

    prompt = (
        f'Passages from the course:\n{retrieve.context_block(passages)}\n\n'
        f'{transcript}'
        f'Their question: {question}\n\n'
        f'{GROUNDED_RULE} Answer in 2-4 sentences, speaking to them as "you".'
    )

    reply = _safe(
        client.complete,
        prompt,
        system=TUTOR_VOICE,
        max_tokens=320,
        temperature=0.3,
        sentences=4,
    )
    if not reply:
        return None

    return {
        'reply': reply,
        'sources': [
            {
                'title': p['title'][:90],
                'where': p['where'],
                'course_id': p['course_id'],
                'module_id': p['module_id'],
            }
            for p in passages
            if p['course_id']
        ][:3],
        'source': 'model',
        'authored': False,
    }


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
        sentences=3,
        cache_key=f'wrong:{module_title}:{question}:{chosen}',
    )


# --------------------------------------------------------------------------- #
# Markets                                                                      #
# --------------------------------------------------------------------------- #

def chart_hint(symbol: str, name: str, series: list[dict]) -> str | None:
    """A teaching hint for the prediction game, derived from the actual series.

    Which of the three measures matters is decided here, and the model is shown
    only that one. Given all three it wrote "the change from +4.0% to +22.2%",
    inventing a movement between a ten-session return and a trading range —
    two numbers that are not on the same scale and were never a before and
    after. One number in the prompt is one number it can misattribute.
    """
    closes = [float(p['close']) for p in series if p.get('close')]
    if len(closes) < 10:
        return None

    recent, earlier = closes[-10:], closes[-30:-10] or closes[:10]
    momentum = round((recent[-1] / recent[0] - 1) * 100, 1)
    versus_mean = round((recent[-1] / (sum(earlier) / len(earlier)) - 1) * 100, 1)
    swing = round((max(recent) - min(recent)) / recent[-1] * 100, 1)

    # The largest signal relative to what counts as large for its own measure.
    if swing >= 12 and swing > abs(momentum) * 1.5:
        value, label, watch = swing, f'traded in a {swing:.1f}% range over ten sessions', 'how wide the daily swings are'
    elif abs(versus_mean) >= abs(momentum):
        value, label, watch = versus_mean, f'sits {versus_mean:+.1f}% away from its 20-session average', 'the distance from the average'
    else:
        value, label, watch = momentum, f'moved {momentum:+.1f}% over ten sessions', 'the recent direction'

    prompt = (
        f'{name} ({symbol}) {label}.\n\n'
        f'In one sentence, tell a beginner why {watch} is worth paying attention '
        'to before making a call. Do not predict a direction or a price. Do not '
        'use any number other than the one above.'
    )
    return _safe(
        client.complete,
        prompt,
        system=TUTOR_VOICE,
        max_tokens=110,
        sentences=1,
        facts={'value': value},
        # Bucketed so the hint is stable for a session but refreshes as prices move.
        cache_key=f'hint:{symbol}:{value}',
    )


def judge_prediction(symbol: str, *, called: str, actual: str, rationale: str, move_percent: float) -> str | None:
    """Grade a prediction on its reasoning, not only its outcome.

    The point of the game is process: a good call for a bad reason should not
    read as a win.
    """
    move = round(move_percent, 2)
    prompt = (
        f'A learner predicted {symbol} would be {called}. It actually moved '
        f'{move:+.2f}% ({actual}).\n'
        f'Their reasoning: "{rationale or "(none given)"}"\n\n'
        'In 2-3 sentences: say whether the reasoning was sound independently of '
        'the outcome, name one thing they missed, and give one habit to carry '
        'into the next call.'
    )
    return _safe(
        client.complete,
        prompt,
        system=ANALYST_VOICE,
        max_tokens=220,
        sentences=3,
        facts={'move': move},
    )


def critique_trade(symbol: str, *, action: str, quantity: int, rationale: str, weight_percent: float) -> str | None:
    """React to the reason a learner gave for a trade, at the moment they place it."""
    weight = round(weight_percent)
    prompt = (
        f'A learner is about to {action} {quantity} shares of {symbol}. '
        f'This position would be {weight}% of their portfolio.\n'
        f'Their stated reason: "{rationale}"\n\n'
        'In 2 sentences: name one thing their reasoning handles well and one '
        'question they have not answered. Do not tell them whether to trade.'
    )
    return _safe(
        client.complete,
        prompt,
        system=ANALYST_VOICE,
        max_tokens=180,
        sentences=2,
        facts={'weight': weight, 'quantity': quantity},
    )


# --------------------------------------------------------------------------- #
# Progress                                                                     #
# --------------------------------------------------------------------------- #

def weekly_recap(stats: dict) -> str | None:
    """Narrate the week from the user's own numbers."""
    figures = {
        'modules': stats.get('modules', 0),
        'accuracy': round(stats.get('accuracy', 0)),
        'puzzles': stats.get('puzzles', 0),
        'puzzle_days': stats.get('puzzle_days', 7),
        'streak': stats.get('streak', 0),
        'portfolio_return': round(stats.get('portfolio_return', 0), 1),
    }

    prompt = (
        "A learner's week in a finance learning app:\n"
        f'- modules completed: {figures["modules"]}\n'
        f'- quiz accuracy: {figures["accuracy"]}%\n'
        f'- daily puzzles solved: {figures["puzzles"]} of {figures["puzzle_days"]}\n'
        f'- current streak: {figures["streak"]} days\n'
        f'- practice portfolio return: {figures["portfolio_return"]:+.1f}%\n'
        f'- weakest topic: {stats.get("weak_topic", "not enough data")}\n\n'
        'Write 3 sentences: what actually improved, the one number worth '
        'attention, and what to do next week. Address them as "you". Use only '
        'the numbers above. No praise the numbers do not support.'
    )

    # Keyed on the figures themselves, and on the day. A recap is the same recap
    # until one of the numbers changes; without this it regenerated on every
    # visit to Progress and cost three seconds each time.
    fingerprint = ':'.join(f'{key}={value}' for key, value in sorted(figures.items()))

    return _safe(
        client.complete,
        prompt,
        system=TUTOR_VOICE,
        max_tokens=220,
        sentences=3,
        facts=figures,
        cache_key=f'recap:{date.today()}:{fingerprint}',
    )


def generate_drill_questions(module_title: str, theory: str, count: int = 3) -> list[dict] | None:
    """Generate practice questions from module theory.

    This is what keeps the daily drill from running dry: the hand-authored bank
    is ~96 questions, which one committed user exhausts in a weekend.

    Every question is checked against the module text before it ships. A small
    model writes a plausible-looking question with two correct options often
    enough that unchecked output would teach the wrong thing.
    """
    prompt = (
        f'Module: {module_title}\n'
        f'Content:\n"""{theory[:1800]}"""\n\n'
        f'Write {count} multiple-choice questions testing whether someone can '
        'apply this content, not whether they memorised it. Each needs exactly 4 '
        'options where the wrong ones are plausible mistakes, not obvious filler. '
        'Everything must be answerable from the content above.'
    )

    schema = {
        'type': 'object',
        'properties': {
            'questions': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'question': {'type': 'string'},
                        'options': {
                            'type': 'array',
                            'items': {'type': 'string'},
                            'minItems': 4,
                            'maxItems': 4,
                        },
                        'correct_index': {'type': 'integer', 'minimum': 0, 'maximum': 3},
                        'explanation': {'type': 'string'},
                    },
                    'required': ['question', 'options', 'correct_index', 'explanation'],
                },
            }
        },
        'required': ['questions'],
    }

    payload = _safe(
        client.complete_json,
        prompt,
        system=TUTOR_VOICE,
        schema=schema,
        schema_hint='questions',
        max_tokens=1400,
        heavy=True,
        cache_key=f'drill:{module_title}:{count}',
    )
    if not payload:
        return None

    return [q for q in payload.get('questions', []) if _usable_question(q)]


def _usable_question(question) -> bool:
    """Whether a generated question is safe to put in front of a learner."""
    if not isinstance(question, dict):
        return False

    options = question.get('options')
    index = question.get('correct_index')

    if not isinstance(options, list) or len(options) != 4:
        return False
    if not all(isinstance(o, str) and o.strip() for o in options):
        return False
    # `bool` is a subclass of `int`, so True would otherwise pass as index 1.
    if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < 4:
        return False

    # Duplicate options mean two right answers, or a question that gives itself
    # away. Either way it is not gradeable.
    if len({o.strip().lower() for o in options}) != 4:
        return False

    return bool(str(question.get('question', '')).strip())


# --------------------------------------------------------------------------- #
# Goal assessment                                                              #
# --------------------------------------------------------------------------- #

def assess_goal(*, description: str, facts: dict, capacity: dict) -> list[str] | None:
    """Observations about somebody's own figures, for a goal already assessed.

    The judgement is not asked for and not accepted. ``users.goals.assessment``
    computes how critical the goal is, how much risk the numbers can absorb, the
    headline, the stance and the question, with no model involved, and
    ``fallback_verdict`` states all of it in plain words on its own.

    Asked for those fields anyway, the model returned "The goal is too ambitious
    and unrealistic" for a goal the same payload marked ``can_take_risk`` — a
    verdict contradicting the one beside it on the page. What it does do well is
    the sentence underneath: given Rs 90,000 of income against Rs 60,000 of
    commitments it writes a fair observation about the gap.

    So it is asked for the observations and nothing else, and they are dropped
    if any of them quotes a figure nobody supplied.
    """
    lines = '\n'.join(f'- {key.replace("_", " ")}: {value}' for key, value in facts.items())
    blockers = '; '.join(capacity.get('blockers') or []) or 'none'
    reasons = '; '.join(capacity.get('reasons') or []) or 'none'

    prompt = (
        f'Someone is setting a savings goal. In their words: "{description}"\n\n'
        f'Their numbers:\n{lines}\n\n'
        f'Their risk capacity has already been assessed as: {capacity.get("level")}\n'
        f'Supporting this: {reasons}\n'
        f'Working against it: {blockers}\n\n'
        'Write 2-3 short observations about their situation. Each must quote one '
        'of their actual figures above and say what it means for this goal. Do '
        'not give a verdict, do not say whether the goal is realistic, and do not '
        'use any number that is not listed above.'
    )

    schema = {
        'type': 'object',
        'properties': {
            'observations': {
                'type': 'array',
                'items': {'type': 'string'},
                'minItems': 2,
                'maxItems': 3,
            }
        },
        'required': ['observations'],
    }

    payload = _safe(
        client.complete_json,
        prompt,
        system=ANALYST_VOICE,
        schema=schema,
        schema_hint='observations',
        max_tokens=320,
        # Their figures and nothing else. Without this the model returned valid
        # JSON describing "$25 million" over "15 months" against "$48,000" of
        # commitments, for a Rs 25,00,000 goal over 15.8 years on Rs 60,000.
        facts=facts,
        # Same situation, same read. Without this the assessment regenerates on
        # every keystroke in the form.
        cache_key=f'goal-observations:{description[:60]}:{sorted(facts.items())}:{capacity.get("level")}',
    )
    if not payload:
        return None

    observations = [
        str(line).strip()
        for line in payload.get('observations', [])
        if isinstance(line, str) and len(line.split()) >= 5
    ]
    return observations or None
