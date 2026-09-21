"""
Help that follows the user around.

:mod:`ai.tutor` holds one function per existing feature. This holds the ones
whose whole purpose is that help is available wherever somebody happens to be
stuck — a word they do not know, a number on screen they cannot place, a page
they have opened without knowing what to do on it.

Which of these use the model, and why some do not
-------------------------------------------------
Every function here was written against the model first and then measured. Two
of them were taken off it, because the measurement said so:

* **Page orientation** is the same advice for everybody in the same situation.
  Asked to write it, the model told a user with Rs 24,000 of cash to save
  "$24000 towards your target of a monthly number". The guidance is now written
  out, and which paragraph appears is decided by the user's own figures.
* **Explaining a number on screen** is a fixed set of statistics this app
  computes. Asked what a diversification score of 31 out of 100 meant, the model
  answered that "a diversified portfolio has an average return rate of about
  31%" — it read a score as a return. Those are written out too.

What is left on the model is what it is good at: rewriting a retrieved passage
into an answer, and putting computed figures into a sentence. Definitions come
from :mod:`ai.glossary`, knowledge from :mod:`ai.retrieve`, figures from the
caller, and :mod:`ai.guard` rejects anything numeric that was invented.
"""

from __future__ import annotations

import logging

from . import client, glossary, retrieve
from .tutor import TUTOR_VOICE, _safe

logger = logging.getLogger(__name__)

# What each section is for, in the app's own terms. The model cannot infer this
# from a URL and guesses badly when asked to.
ZONES = {
    'today': 'the daily set — one lesson, a puzzle and a market question',
    'learn': 'the course library, where modules are read and quizzed',
    'markets': 'the practice trading terminal, with virtual money only',
    'play': 'the games — scenarios, the oracle, daily puzzles',
    'goals': 'goal planning, where a target becomes a monthly number',
    'progress': 'the record of what has been learned and how accurately',
}


# --------------------------------------------------------------------------- #
# Terms                                                                        #
# --------------------------------------------------------------------------- #

def explain(term: str, *, context: str = '', course_id: str = '') -> dict | None:
    """Explain a term or a phrase.

    This is the surface a learner reaches for most: they are mid-sentence, a
    word means nothing to them, and leaving the page to look it up is how a
    session ends.

    Three sources, in order of how much they can be trusted: the glossary, the
    course content, then nothing. There is no fourth step where the model
    answers from its own memory — asked to define "quantum arbitrage swap", a
    phrase with no meaning, it produced a confident paragraph about quantum
    computing and favourable prices. A term this app cannot source is a term it
    says it does not know.

    ``context`` is the sentence the term appeared in, which disambiguates the
    short ones — "margin" in a trading module and in a business module are not
    the same word.
    """
    term = (term or '').strip()
    if not term:
        return None

    # Returned as written. A definition is the thing this model is least able to
    # produce, and rewriting a correct one can only make it worse.
    entry = glossary.look_up(term)
    if entry:
        return {
            'term': entry['term'],
            'explanation': f'{entry["definition"]}\n\n{entry["example"]}',
            'source': 'glossary',
            'sources': [],
        }

    passages = retrieve.search(f'{term} {context}'.strip(), limit=3, course_id=course_id)
    if not passages:
        return {
            'term': term,
            'explanation': (
                f'The course does not cover "{term}" yet, so I would rather say '
                'that than guess at it.'
            ),
            'source': 'unknown',
            'sources': [],
        }

    prompt = (
        f'Passages from the course:\n{retrieve.context_block(passages, budget=1000)}\n\n'
        f'A learner highlighted "{term}"'
        + (f' while reading: "{context[:200]}"' if context else '')
        + '.\n\nExplain it in 2-3 sentences using only the passages above.'
    )

    text = _safe(
        client.complete,
        prompt,
        system=TUTOR_VOICE,
        max_tokens=220,
        temperature=0.3,
        sentences=3,
        cache_key=f'explain:{term.lower()}:{course_id}',
    )
    if not text:
        return None

    return {
        'term': term,
        'explanation': text,
        'source': 'course',
        'sources': [
            {'title': p['title'][:90], 'where': p['where'],
             'course_id': p['course_id'], 'module_id': p['module_id']}
            for p in passages
        ][:2],
    }


# --------------------------------------------------------------------------- #
# Numbers on screen                                                            #
# --------------------------------------------------------------------------- #

# The statistics this app computes, explained once. A fixed list needs a fixed
# answer, not a fresh guess every time somebody taps the same icon.
METRICS = {
    'diversification score': (
        'How evenly your money is spread across sectors, from 0 to 100. A single '
        'holding scores 0; an even spread across many sectors approaches 100. It '
        'says nothing about returns — a well-spread portfolio can still fall.',
        'It rises when you add holdings in sectors you do not already own, and '
        'falls when you add more of what you have most of.',
    ),
    'concentration grade': (
        'A letter for the same diversification score: A is well spread, D means '
        'most of your money depends on one sector.',
        'It moves only when the balance between sectors changes, not when prices do.',
    ),
    'monthly required': (
        'What you would have to put aside each month to reach this goal on time, '
        'given what you have saved and the return the plan assumes.',
        'It falls if you extend the date, lower the target, or start from a larger '
        'amount. It rises for every month you wait.',
    ),
    'calibration': (
        'How well your confidence matches your accuracy. Being right 70% of the '
        'time when you said you were 70% sure is perfect calibration, even though '
        'you were wrong three times in ten.',
        'It improves when you lower your confidence on the calls you get wrong — '
        'not by being right more often.',
    ),
    'quiz accuracy': (
        'The share of quiz questions you have answered correctly.',
        'Reviews raise it more reliably than new modules do, because a question '
        'you got wrong is the one most likely to come back.',
    ),
    'streak': (
        'Consecutive days you have finished the daily set.',
        'It resets on a missed day. It measures turning up, not understanding.',
    ),
    'esg score': (
        'A value-weighted average of the sector profiles you hold, illustrative '
        'rather than a rating agency score.',
        'It shifts with the sector mix of your holdings, weighted by position size.',
    ),
    'total return': (
        'What your practice account is worth against what you put into it, as a '
        'percentage.',
        'Unrealised gains count, so it moves with prices even on days you do not trade.',
    ),
}

_METRIC_ALIASES = {
    'diversification': 'diversification score',
    'spread score': 'diversification score',
    'grade': 'concentration grade',
    'monthly amount': 'monthly required',
    'monthly investment': 'monthly required',
    'sip amount': 'monthly required',
    'accuracy': 'quiz accuracy',
    'day streak': 'streak',
    'return': 'total return',
    'portfolio return': 'total return',
}


def explain_number(label: str, value, *, context: str = '') -> str | None:
    """Explain one figure on screen: what it measures and what would move it.

    Attached to the computed statistics, which are exactly the numbers a
    beginner reads without knowing whether 31 is good.

    Answered from :data:`METRICS` where the label is one this app computes. The
    model is only asked about a label that is not in the list, and is given the
    number rather than asked to interpret it — handed "Diversification score:
    31" it replied that the portfolio "has an average return rate of about 31%".
    """
    label = (label or '').strip()
    if not label:
        return None

    key = label.lower().strip()
    key = _METRIC_ALIASES.get(key, key)

    entry = METRICS.get(key)
    if entry is None:
        for name in METRICS:
            if name in key or key in name:
                entry = METRICS[name]
                break

    if entry:
        meaning, moves = entry
        return f'{meaning} {moves}'

    prompt = (
        f'A number on screen reads "{label}: {value}".'
        + (f' Context: {context[:200]}' if context else '')
        + '\n\nIn 2 sentences: say what this measures and what would change it. '
        'Do not interpret the number itself.'
    )
    return _safe(
        client.complete,
        prompt,
        system=TUTOR_VOICE,
        max_tokens=160,
        temperature=0.3,
        sentences=2,
        cache_key=f'explain-number:{label}',
    )


# --------------------------------------------------------------------------- #
# Orientation                                                                  #
# --------------------------------------------------------------------------- #

def page_help(zone: str, *, facts: dict | None = None) -> str | None:
    """What to do on the page the user is looking at, given their own numbers.

    Written out rather than generated. The advice for somebody on the markets
    page with no holdings is the same advice every time, and a model asked to
    produce it invented a currency and a target that did not exist.

    Which paragraph appears is decided by the user's figures, so it is still
    about them — it is the selection that is personal, not the prose.
    """
    if zone not in ZONES:
        return None

    numbers = facts or {}
    chooser = _GUIDANCE.get(zone)
    return chooser(numbers) if chooser else None


def _number(facts: dict, key: str, default: float = 0.0) -> float:
    value = facts.get(key, default)
    return float(value) if isinstance(value, (int, float)) else default


def _markets_help(facts: dict) -> str:
    holdings = _number(facts, 'holdings')
    top_weight = _number(facts, 'top_weight_percent')

    if holdings == 0:
        return (
            'Nothing is invested yet, so start with one position small enough that '
            'being wrong about it would not bother you. Write down why you bought '
            'before you buy — the reason is what you grade later, not the outcome.'
        )
    if top_weight >= 55:
        return (
            f'One sector is {top_weight:.0f}% of your holdings, so a single shock '
            'moves almost everything you own. Adding a position in a sector you do '
            'not hold does more for your risk than picking a better stock in the '
            'one you already do.'
        )
    if holdings < 3:
        return (
            'With this few positions, each one dominates the result and you cannot '
            'tell a good decision from a lucky one. Widening the portfolio makes '
            'your own track record readable.'
        )
    return (
        'Check the analysis tab before trading rather than after: it names the '
        'concentration you have built up, which is the risk that actually decides '
        'your returns. Then use the trade note to record why, so the review has '
        'something to grade.'
    )


def _goals_help(facts: dict) -> str:
    goals = _number(facts, 'goals')
    if goals == 0:
        return (
            'Set one goal with a real date and a real amount. A target without a '
            'date cannot be turned into a monthly number, and the monthly number '
            'is the only part you actually act on.'
        )
    return (
        'Open the plan and look at the monthly figure rather than the total — that '
        'is the commitment you are making. If it is uncomfortable, move the date '
        'before you move the risk.'
    )


def _learn_help(facts: dict) -> str:
    due = _number(facts, 'due_reviews')
    if due > 0:
        return (
            f'You have {due:.0f} review{"s" if due != 1 else ""} due. Clearing '
            'those first is worth more than a new module: a question you once got '
            'wrong is the one most likely to go wrong again.'
        )
    return (
        'Read one module and take its quiz in the same sitting. Reading without '
        'the quiz feels like learning and does not survive the week.'
    )


def _today_help(facts: dict) -> str:
    streak = _number(facts, 'streak')
    if streak >= 3:
        return (
            f'You are {streak:.0f} days in. Finish the set before you open anything '
            'else — it takes a few minutes and it is what the streak measures.'
        )
    return (
        'The daily set is one lesson, one puzzle and one market question. Doing all '
        'three is what builds the habit; doing the easy one is what breaks it.'
    )


def _play_help(facts: dict) -> str:
    return (
        'Scenarios are where a decision costs nothing, so make the one you would '
        'actually make rather than the one you think is correct. The debrief is '
        'only useful if the choice was honest.'
    )


def _progress_help(facts: dict) -> str:
    accuracy = _number(facts, 'accuracy')
    if accuracy and accuracy < 60:
        return (
            f'Accuracy is {accuracy:.0f}%, which usually means moving through '
            'modules faster than they are sticking. Slow down and clear the '
            'reviews before starting anything new.'
        )
    return (
        'Look at calibration rather than accuracy. Being right 70% of the time '
        'while claiming to be certain is a worse habit than being right less often '
        'and knowing it.'
    )


_GUIDANCE = {
    'today': _today_help,
    'learn': _learn_help,
    'markets': _markets_help,
    'play': _play_help,
    'goals': _goals_help,
    'progress': _progress_help,
}


# --------------------------------------------------------------------------- #
# Written from the user's own figures                                          #
# --------------------------------------------------------------------------- #

def daily_brief(*, name: str, stats: dict) -> str | None:
    """A short personal opening for the day, written from real progress.

    The figures are the caller's. The model decides only which of them to lead
    with and how to say it, and the guard drops the answer if it reaches for a
    number nobody gave it.
    """
    figures = {
        'streak': int(stats.get('streak', 0)),
        'modules_done': int(stats.get('modules_done', 0)),
        'accuracy': round(float(stats.get('accuracy', 0))),
        'due_reviews': int(stats.get('due_reviews', 0)),
        'portfolio_return': round(float(stats.get('portfolio_return', 0)), 1),
    }
    weak = stats.get('weak_topic') or ''

    prompt = (
        f'{name} is opening a finance learning app today.\n'
        f'- day streak: {figures["streak"]}\n'
        f'- modules finished: {figures["modules_done"]}\n'
        f'- quiz accuracy: {figures["accuracy"]}%\n'
        f'- reviews due today: {figures["due_reviews"]}\n'
        f'- practice portfolio: {figures["portfolio_return"]:+.1f}%\n'
        + (f'- weakest topic: {weak}\n' if weak else '')
        + '\nWrite 2 sentences: name the one thing worth doing today and why, '
        'using their numbers. Address them as "you". No greeting, and no praise '
        'the numbers do not support.'
    )

    return _safe(
        client.complete,
        prompt,
        system=TUTOR_VOICE,
        max_tokens=170,
        temperature=0.5,
        sentences=2,
        facts=figures,
        cache_key=f'brief:{name}:{sorted(figures.items())}:{weak}',
    )


def scenario_debrief(*, title: str, choice: str, outcome: str, principle: str) -> str | None:
    """Close a scenario by naming the principle the choice just demonstrated.

    The principle is authored with the scenario, so this is rephrasing against
    what the learner actually picked rather than deciding what the lesson was.
    """
    prompt = (
        f'Scenario: {title}\n'
        f'They chose: {choice}\n'
        f'What happened: {outcome}\n'
        f'The principle this teaches: {principle}\n\n'
        'In 2 sentences, connect their choice to the principle and give one '
        'situation outside this game where the same reasoning applies.'
    )
    return _safe(
        client.complete,
        prompt,
        system=TUTOR_VOICE,
        max_tokens=180,
        temperature=0.4,
        sentences=2,
        cache_key=f'debrief:{title}:{choice}',
    )
