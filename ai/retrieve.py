"""
Search over the course content, so the mentor answers from what we wrote.

Why this exists
---------------
Asked "what is an index fund?", the local model replies that an index fund is
"also known as an ETF" and "represents shares of a single underlying stock",
then cites the S&P 500 to a user in India. Every clause of that is wrong. A
half-billion-parameter model does not carry reliable finance knowledge, and no
amount of prompting puts knowledge into it that is not there.

What it does carry is the ability to read a short passage and rewrite it for
somebody. So the passage has to come from us. This module searches the 60
authored modules — their theory and their question-and-answer pairs — and hands
the best few to the model as the only material it is allowed to use.

The retrieval is plain BM25 over word stems. No embedding model, no vector
store, no service to keep running: the corpus is a few hundred short passages,
it is already parsed and cached by :mod:`courses.content`, and scoring all of
them takes about a millisecond. Reaching for anything heavier would be cost
without a benefit.
"""

from __future__ import annotations

import math
import re
from functools import lru_cache

from courses import content

# BM25's usual constants. k1 controls how fast repeated terms stop helping, b
# how much a long passage is penalised for its length.
K1 = 1.5
B = 0.75

WORD = re.compile(r"[a-z0-9']+")

# Words carried by almost every passage in a finance corpus, so matching on them
# says nothing about relevance.
STOPWORDS = frozenset("""
a an and are as at be been but by can do does for from had has have how i if in
into is it its may more no not of on or should so some such than that the their
them then there these they this to was what when where which who why will with
you your yours we our us me my
""".split())

MIN_SCORE = 1.2


# Endings stripped to fold a word to its stem, longest first. Deliberately
# short: this is not a stemmer, it is the four endings that actually cost
# matches in a finance corpus.
#
# Without "ing", "what is compounding?" does not reach the passage that defines
# compound interest, and the model — left with three passages about SIPs —
# answered that compounding is "new money entering the market continuously".
# The corpus had the right answer the whole time and search could not see it.
SUFFIXES = ('ing', 'es', 'ed', 's')
MIN_STEM = 4


def _tokens(text: str) -> list[str]:
    """Lower-cased words, stopwords dropped, folded to a rough stem.

    Folding stays crude on purpose. A real stemmer is a dependency, and the
    cases it would buy over these four endings are rare enough in this corpus to
    be worth less than the clarity.
    """
    words = []
    for word in WORD.findall(text.lower()):
        if word in STOPWORDS or len(word) < 2:
            continue
        for suffix in SUFFIXES:
            if word.endswith(suffix) and len(word) - len(suffix) >= MIN_STEM:
                # "ss" is not a plural: "loss" must not become "lo".
                if suffix == 's' and word.endswith('ss'):
                    break
                word = word[: -len(suffix)]
                break
        words.append(word)
    return words


@lru_cache(maxsize=1)
def _index() -> dict:
    """Build the searchable passage list once per process.

    Rebuilt by :func:`reload`, which the content loader calls when the files on
    disk change.
    """
    passages: list[dict] = []

    for course in content.catalogue():
        for module in course['modules']:
            where = f"{course['title']} · {module['title']}"
            link = {'course_id': course['id'], 'module_id': module['id'],
                    'course_title': course['title'], 'module_title': module['title']}

            for card in module['cards']:
                body = content.clean(card.get('answer', ''))
                if body:
                    passages.append({
                        'text': body,
                        'title': card.get('prompt') or module['title'],
                        'kind': 'theory',
                        'where': where,
                        **link,
                    })

            for pair in module['qna']:
                answer = content.clean(pair.get('answer', ''))
                if not answer:
                    continue
                explanation = content.clean(pair.get('explanation', ''))
                passages.append({
                    # The question is indexed with the answer because a learner's
                    # phrasing matches the question far more often than the prose.
                    'text': f"{answer} {explanation}".strip(),
                    'title': pair.get('question', ''),
                    'kind': 'qna',
                    'where': where,
                    **link,
                })

    document_frequency: dict[str, int] = {}
    for passage in passages:
        passage['tokens'] = _tokens(f"{passage['title']} {passage['text']}")
        for term in set(passage['tokens']):
            document_frequency[term] = document_frequency.get(term, 0) + 1

    total = len(passages) or 1
    average_length = sum(len(p['tokens']) for p in passages) / total

    return {
        'passages': passages,
        'idf': {
            term: math.log(1 + (total - count + 0.5) / (count + 0.5))
            for term, count in document_frequency.items()
        },
        'average_length': average_length or 1,
    }


def reload() -> None:
    """Drop the index after content changes on disk."""
    _index.cache_clear()


def search(query: str, *, limit: int = 3, course_id: str = '') -> list[dict]:
    """The passages most likely to answer ``query``.

    ``course_id`` biases towards the course being read without excluding the
    rest, because the answer to "what is compounding?" asked inside a tax module
    still lives in the investing one.
    """
    terms = _tokens(query)
    if not terms:
        return []

    index = _index()
    idf = index['idf']
    average_length = index['average_length']

    scored = []
    for passage in index['passages']:
        tokens = passage['tokens']
        if not tokens:
            continue

        length_norm = K1 * (1 - B + B * len(tokens) / average_length)
        score = 0.0
        for term in terms:
            weight = idf.get(term)
            if weight is None:
                continue
            frequency = tokens.count(term)
            if frequency:
                score += weight * frequency * (K1 + 1) / (frequency + length_norm)

        if score <= 0:
            continue
        if course_id and passage['course_id'] == course_id:
            score *= 1.25
        scored.append((score, passage))

    scored.sort(key=lambda pair: pair[0], reverse=True)

    return [
        {
            'text': passage['text'],
            'title': passage['title'],
            'kind': passage['kind'],
            'where': passage['where'],
            'course_id': passage['course_id'],
            'module_id': passage['module_id'],
            'course_title': passage['course_title'],
            'module_title': passage['module_title'],
            'score': round(score, 2),
        }
        for score, passage in scored[:limit]
        if score >= MIN_SCORE
    ]


# How much of a learner's wording has to match an authored question before its
# answer is served verbatim. High enough that a wrong match is unlikely, low
# enough that rephrasing still finds it.
#
# Measured against a plain word overlap, which cannot tell these apart:
#   "How big should my emergency fund be?" vs "When should I use my emergency
#   fund?" — two words of three shared, and the wrong answer served with
#   confidence. The shared words are the common ones; the word carrying the
#   question ("big" against "use") is the rare one. Weighting by rarity
#   separates them, and the threshold is set between where the two land:
#
#   0.50  "Is a SIP safer than a lump sum?" -> the authored lump-sum question
#   0.40  the emergency-fund near-miss above
#   0.00  "how do i cook pasta"
#
# A miss costs nothing: the question falls through to ordinary retrieval, which
# is the path every question took before this existed.
DIRECT_MATCH = 0.45


def direct_answer(question: str) -> dict | None:
    """An authored answer to this exact question, if one was written.

    Worth checking before the model is involved at all. Asked "how big should my
    emergency fund be?", the model paraphrased the retrieved passage into "you
    should have a large portion of your emergency savings in stocks" — an
    inversion of what the passage said, and advice that would hurt somebody.
    The authored answer cannot invert itself, costs no time, and is what a
    subject expert already wrote for this exact question.

    Matching is on the question wording rather than BM25 over the answer,
    because "what is a credit score" should hit the card titled the same way,
    not the longest passage containing the word "credit".

    The overlap is weighted by how rare each word is in the corpus. Unweighted,
    "emergency" and "fund" outvote the one word that says what is being asked.
    """
    asked = set(_tokens(question))
    if not asked:
        return None

    index = _index()
    idf = index['idf']
    # A word the corpus has never seen is the most distinguishing kind there is,
    # so it is weighted above every word that appears in it.
    unseen = max(idf.values(), default=1.0)

    def weight(words) -> float:
        return sum(idf.get(word, unseen) for word in words)

    best_score, best = 0.0, None
    for passage in index['passages']:
        if passage['kind'] != 'qna':
            continue
        candidate = set(_tokens(passage['title']))
        if not candidate:
            continue

        union = weight(asked | candidate)
        overlap = weight(asked & candidate) / union if union else 0.0
        if overlap > best_score:
            best_score, best = overlap, passage

    if best is None or best_score < DIRECT_MATCH:
        return None

    return {
        'answer': best['text'],
        'title': best['title'],
        'where': best['where'],
        'course_id': best['course_id'],
        'module_id': best['module_id'],
        'match': round(best_score, 2),
    }


def context_block(passages: list[dict], *, budget: int = 1400) -> str:
    """Passages as prompt text, trimmed to a budget.

    Numbered because the model is asked to cite which one it used, and a number
    is the only citation format small models get right consistently.
    """
    lines, used = [], 0
    for position, passage in enumerate(passages, start=1):
        body = passage['text']
        if used + len(body) > budget:
            body = body[: max(0, budget - used)].rsplit(' ', 1)[0]
        if not body:
            break
        lines.append(f"[{position}] {passage['title']}\n{body}")
        used += len(body)
    return '\n\n'.join(lines)
