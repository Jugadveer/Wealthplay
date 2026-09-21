"""
What stands between a half-billion-parameter model and the user.

The local model is fast, free and private, and it is also small enough to get
arithmetic wrong with total confidence. Measured on this app's own prompts, it
answers "Rs 2,88,000" for the future value of Rs 5,000 a month over ten years
at 12%, which is off by about nine lakh. It writes markdown after being told
not to. It stops mid-word when it reaches the token budget.

None of that has to reach a page, because none of it is the model's job here.
Python computes the figures; the model writes the sentence around them. This
module enforces that split:

* :func:`tidy` fixes the presentation problems — markdown, preamble, a sentence
  that ends in the middle of a word.
* :func:`grounded` catches the dangerous one. Every money figure, rate and
  decimal in a reply has to trace back to a number the caller supplied. A reply
  that invents one is rejected, and the caller shows its computed text instead.

The check deliberately ignores bare small integers. "Two things stand out" is
prose, not a claim about someone's money, and rejecting it would mean rejecting
almost everything. What gets checked is what can do damage: anything carrying a
rupee sign, a percent sign, a decimal point, or four digits.
"""

from __future__ import annotations

import re

# Abbreviations whose full stop does not end a sentence. Masked before splitting
# and restored after, which is shorter than a lookbehind for each one and does
# not break the moment somebody adds another.
ABBREVIATIONS = ('Rs.', 'e.g.', 'i.e.', 'vs.', 'approx.', 'etc.', 'Dr.', 'Mr.', 'Ms.')
_MASK = '\x00'

# Lines where the model has stopped answering and started reciting the prompt
# back. Observed in the wild as a reply ending "Learner asks: What is
# compounding? Answer only from the numbered passages."
LEAKED = re.compile(
    r'^\s*(?:learner(?:\s+asks?)?|nex|passages?(?:\s+from[^:\n]*)?|question|module|context|'
    r'answer only[^\n]*|\[\d+\])\s*:?\s*',
    re.I,
)

# Openers a small model reaches for despite being told not to.
PREAMBLE = re.compile(
    r'^\s*(?:sure|certainly|of course|absolutely|great question|good question|here(?:\'s| is)'
    r'(?: the| a| an)?[^:.\n]*|okay|ok)\s*[,.!:—-]+\s*',
    re.I,
)

# A number with whatever marks it as money, a rate, a magnitude or a span of
# time. Time is in here because "15 months" for a horizon of 15.8 years is the
# same class of error as a wrong rupee figure, and a bare 15 would otherwise be
# dismissed as prose counting.
FIGURE = re.compile(
    r'(?P<currency>(?:Rs\.?|₹|INR)\s*)?'
    r'(?P<number>\d[\d,]*(?:\.\d+)?)'
    r'\s*(?P<suffix>%|per\s?cent|rupees?|lakhs?|crores?|k\b'
    r'|years?|months?|weeks?|days?)?',
    re.I,
)

SCALE = {'lakh': 100_000, 'lakhs': 100_000, 'crore': 10_000_000, 'crores': 10_000_000, 'k': 1_000}

# Numbers that are never a claim about the user's money.
YEAR_RANGE = range(1900, 2101)


# --------------------------------------------------------------------------- #
# Presentation                                                                 #
# --------------------------------------------------------------------------- #

def tidy(text: str, *, sentences: int = 0) -> str:
    """Clean a raw completion into something publishable.

    Strips markdown and preamble, repairs a mid-word cut-off, and caps the
    length the prompt asked for but the model ignored.
    """
    if not text:
        return ''

    text = text.strip()
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.M)      # headings
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text, flags=re.S)  # bold
    text = re.sub(r'(?<!\w)__(.+?)__(?!\w)', r'\1', text, flags=re.S)
    text = re.sub(r'`{1,3}', '', text)                       # stray code marks
    text = re.sub(r'^\s*[-*]\s+', '', text, flags=re.M)      # bullet markers
    # Twice, because "Sure! Here is the answer:" is two openers stacked and one
    # pass leaves the second standing.
    text = PREAMBLE.sub('', PREAMBLE.sub('', text))
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]{2,}', ' ', text).strip()

    text = _drop_leaked_scaffolding(text)
    text = _repair_truncation(text)

    # Stripping "Sure! " off the front leaves the sentence starting in
    # lower case, which reads as a bug rather than as an answer.
    #
    # Only for prose. Applied to every string in a structured response it
    # capitalised the enum fields too, turning "can_take_risk" into
    # "Can_take_risk" and failing the schema the model had just satisfied.
    if text and text[0].islower() and _is_prose(text):
        text = text[0].upper() + text[1:]

    if sentences > 0:
        # A caller asking for two sentences wants prose. Asked "how big should
        # my emergency fund be?", the model answered in two sentences and then
        # appended headed sections on debt, insurance, retirement and school
        # fees. Everything after the first paragraph is that habit, and the
        # sentence cap never caught it because the list items had no full stops.
        text = text.split('\n\n')[0].strip()

        parts = split_sentences(text)
        if len(parts) > sentences:
            text = ' '.join(parts[:sentences])

    return text.strip()


def _is_prose(text: str) -> bool:
    """Whether a string is a sentence rather than a machine-readable value.

    An enum member, a slug or an id has no spaces and often carries an
    underscore or a hyphen. Anything with a space is being read by a person.
    """
    return ' ' in text.strip() and '_' not in text.split()[0]


def _drop_leaked_scaffolding(text: str) -> str:
    """Remove lines that echo the prompt rather than answer it."""
    kept = [line for line in text.splitlines() if not LEAKED.match(line)]
    cleaned = '\n'.join(kept).strip()

    # The echo also arrives mid-line, appended to a finished answer.
    cleaned = re.split(r'(?:^|\s)(?:Learner asks|Learner|Answer only from)\s*:', cleaned, maxsplit=1)[0]
    return cleaned.strip()


def split_sentences(text: str) -> list[str]:
    """Sentences, without treating "Rs." or "e.g." as the end of one."""
    masked = text
    for index, abbreviation in enumerate(ABBREVIATIONS):
        masked = masked.replace(abbreviation, f'{_MASK}{index}{_MASK}')

    parts = re.split(r'(?<=[.!?])\s+', masked)

    restored = []
    for part in parts:
        for index, abbreviation in enumerate(ABBREVIATIONS):
            part = part.replace(f'{_MASK}{index}{_MASK}', abbreviation)
        if part.strip():
            restored.append(part.strip())
    return restored


TERMINALS = ('.', '!', '?', '"', "'", ')', ']', ':')


def _repair_truncation(text: str) -> str:
    """Drop a trailing fragment left behind when the token budget ran out.

    Split on real sentence boundaries rather than the last full stop, because
    the last full stop in "Rs. 5,000 is fine" belongs to the abbreviation and
    trimming there would leave the user reading "Rs.".

    A fragment containing a line break is left alone: that is a list or a second
    paragraph, not a sentence cut in half.
    """
    parts = split_sentences(text)
    if len(parts) < 2:
        return text

    last = parts[-1]
    if '\n' in last or last.endswith(TERMINALS):
        return text
    return ' '.join(parts[:-1])


# --------------------------------------------------------------------------- #
# Grounding                                                                    #
# --------------------------------------------------------------------------- #

# This app is in rupees throughout. A dollar sign is never a formatting
# preference here, it is the model having drifted to its training distribution,
# and it arrived alongside "$25 million" for a Rs 25,00,000 goal.
FOREIGN_CURRENCY = re.compile(r'[$€£]\s*\d|\b(?:dollars?|usd|euros?)\b', re.I)

# Institutions and instruments belonging to somebody else's financial system.
# The same drift as the currency, and more convincing: asked how big an
# emergency fund should be, the model recommended "the Emergency Fund
# Calculator provided by the Federal Reserve Bank of New York", which does not
# exist and would not apply here if it did. A learner in India cannot check a
# claim like that, which is exactly why it must not reach them.
FOREIGN_CONTEXT = re.compile(
    r'\b(?:federal reserve|s&p ?500|dow jones|nasdaq|fdic|401\s*\(?k\)?|'
    r'\birs\b|social security|treasury bonds?|wall street|sec\.gov)\b',
    re.I,
)


def drifted(text: str) -> bool:
    """Whether an answer has wandered into another country's financial system.

    Checked on every completion, not only the grounded ones: no surface in this
    app has a reason to mention a US regulator, and the model reaches for them
    whenever the retrieved passages leave it room.
    """
    return bool(FOREIGN_CURRENCY.search(text) or FOREIGN_CONTEXT.search(text))


def tidy_payload(payload):
    """Run :func:`tidy` over every string in a parsed JSON structure."""
    if isinstance(payload, str):
        return tidy(payload)
    if isinstance(payload, dict):
        return {key: tidy_payload(value) for key, value in payload.items()}
    if isinstance(payload, list):
        return [tidy_payload(item) for item in payload]
    return payload


def grounded_payload(payload, facts) -> bool:
    """:func:`grounded`, over every string inside a structured response.

    A JSON schema guarantees the shape of an answer and nothing about its
    truth. This is what checks the contents.
    """
    return all(grounded(text, facts) for text in _strings(payload))


def _strings(node) -> list[str]:
    if isinstance(node, str):
        return [node]
    if isinstance(node, dict):
        return [s for value in node.values() for s in _strings(value)]
    if isinstance(node, (list, tuple)):
        return [s for item in node for s in _strings(item)]
    return []


def grounded(text: str, facts) -> bool:
    """True when every significant figure in ``text`` traces back to ``facts``.

    ``facts`` is whatever the caller computed — a dict, a list, nested or not.
    Its numbers are walked out and expanded to the forms a writer would
    reasonably use: rounded, as a percentage, in lakhs.
    """
    if FOREIGN_CURRENCY.search(text):
        return False

    allowed = _allowed_values(facts)
    return all(_is_allowed(value, allowed) for value in significant_figures(text))


def significant_figures(text: str) -> list[float]:
    """Every number in ``text`` that makes a claim about money, rates or size.

    Bare small integers are skipped: they are how prose counts things, not how
    it quotes a balance.
    """
    found = []
    for match in FIGURE.finditer(text):
        raw = match.group('number')
        try:
            value = float(raw.replace(',', ''))
        except ValueError:
            continue

        suffix = (match.group('suffix') or '').lower().strip().rstrip('.')
        scaled = value * SCALE.get(suffix, 1)

        significant = bool(match.group('currency')) or bool(suffix) or '.' in raw or value >= 1000
        if not significant:
            continue
        if not match.group('currency') and not suffix and int(value) in YEAR_RANGE and value == int(value):
            continue  # a year, not an amount

        found.append(scaled if scaled != value else value)
    return found


def _allowed_values(facts) -> set[float]:
    """Every number the caller vouched for, plus the forms it may be written in."""
    base: set[float] = set()
    _walk(facts, base)

    allowed: set[float] = set()
    for value in base:
        for form in (value, abs(value), value * 100, value / 100):
            allowed.add(round(form, 4))
            allowed.add(float(round(form)))
            allowed.add(round(form, 1))
            allowed.add(round(form, 2))
    return allowed


def _walk(node, into: set[float]) -> None:
    """Collect numbers from any shape of computed payload."""
    if isinstance(node, bool):
        return
    if isinstance(node, (int, float)):
        into.add(float(node))
    elif isinstance(node, dict):
        for value in node.values():
            _walk(value, into)
    elif isinstance(node, (list, tuple, set)):
        for value in node:
            _walk(value, into)
    elif isinstance(node, str):
        for match in FIGURE.finditer(node):
            try:
                into.add(float(match.group('number').replace(',', '')))
            except ValueError:
                continue


def _is_allowed(value: float, allowed: set[float]) -> bool:
    """Whether one figure is close enough to something the caller supplied.

    The tolerance is relative, because rewriting 1,23,456 as "about 1.2 lakh" is
    good writing rather than a hallucination, while turning 8% into 12% is not.
    """
    for candidate in (value, round(value), round(value, 1), round(value, 2)):
        if candidate in allowed:
            return True

    return any(abs(value - other) <= max(0.51, abs(other) * 0.02) for other in allowed)
