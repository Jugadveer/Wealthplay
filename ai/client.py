"""
The single LLM entry point for the whole app.

Why this exists
---------------
Every AI surface used to call a provider directly, each with its own key
handling, its own prompt, and its own silent ``except: pass``. When both
configured models were retired upstream, every one of those surfaces quietly
fell through to a hardcoded template. The UI kept saying "AI" while serving
string interpolation, and nothing logged a warning.

Where the model runs
--------------------
A local ``qwen2.5:0.5b-instruct`` served by Ollama is the primary provider. It
answers in well under a second once warm, costs nothing, needs no key, and
never sends a user's income to anybody else's server. The hosted providers stay
behind it as failover for when Ollama is not running.

What a half-billion-parameter model can and cannot do
-----------------------------------------------------
Measured, not assumed. Asked for the future value of Rs 5,000 a month for ten
years at 12%, it answers Rs 2,88,000; the right answer is about Rs 11.6 lakh.
Given "equity share: 45%" it will explain that as "45% of the monthly cost".
It writes markdown after being told not to, and stops mid-word when it hits the
token budget.

So the division of labour is fixed and not negotiable:

* Python computes every number, every classification and every verdict.
* The model only puts those into a sentence.
* :mod:`ai.guard` then checks the sentence for figures that were never in the
  prompt and rejects it if it finds any.

That is why ``complete`` takes ``facts``: the caller states what is true, and
anything numeric outside that set is treated as invention.

Structured output uses Ollama's ``format`` parameter, which constrains decoding
to the JSON schema rather than asking politely for JSON. That measures 5/5 on
valid syntax where prose prompting does not.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re

import requests
from django.core.cache import cache

from . import guard

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 25
# The local model takes ~25s to load into memory and well under a second once
# resident, so a cold call needs room that a warm one never uses.
OLLAMA_TIMEOUT = 90
# Long enough that ordinary use never pays the load cost twice.
KEEP_ALIVE = '30m'
CACHE_TTL = 60 * 60 * 6

GROQ_URL = 'https://api.groq.com/openai/v1/chat/completions'
GEMINI_URL = 'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'


class NoProviderAvailable(RuntimeError):
    """No configured provider produced a response."""


def _env(name: str, default: str = '') -> str:
    return (os.environ.get(name) or default).strip()


def _groq_keys() -> list[str]:
    keys = [_env('GROQ_API_KEY'), _env('GROQ_API_KEY_2')]
    return [k for k in keys if k]


def _ollama_host() -> str:
    return _env('OLLAMA_HOST', 'http://localhost:11434').rstrip('/')


def _ollama_model() -> str:
    return _env('OLLAMA_MODEL', 'qwen2.5:0.5b-instruct')


# --------------------------------------------------------------------------- #
# Providers                                                                    #
# --------------------------------------------------------------------------- #

# Where a continuation has stopped being an answer. Prompts here carry a
# transcript, and left alone the model writes the learner's next line as well as
# its own — which arrived in the UI as "Learner asks: What is compounding?"
# appended to the reply.
STOP_SEQUENCES = ['\nLearner:', '\nLearner asks:', '\nNex:', '\nPassages:', '\nQuestion:']


def _call_ollama(
    prompt: str,
    system: str,
    temperature: float,
    max_tokens: int,
    schema: dict | None = None,
) -> str | None:
    """Primary provider: the local model.

    Uses ``/api/chat`` rather than ``/api/generate`` so the instruction goes
    through the model's chat template as a user turn. On ``/api/generate`` an
    instruct model treats the prompt as text to continue, which is how prompt
    scaffolding ended up inside answers.

    ``schema`` switches Ollama into constrained decoding, where the sampler can
    only emit tokens that keep the output valid against the schema. Malformed
    JSON stops being a failure mode rather than being handled after the fact.
    """
    messages = ([{'role': 'system', 'content': system}] if system else []) + [
        {'role': 'user', 'content': prompt}
    ]
    body = {
        'model': _ollama_model(),
        'messages': messages,
        'stream': False,
        'keep_alive': KEEP_ALIVE,
        'options': {
            'temperature': temperature,
            'num_predict': max_tokens,
            # A small model repeats itself when left alone; this is the cheapest
            # correction that does not flatten the writing.
            'repeat_penalty': 1.15,
            'top_p': 0.9,
            'stop': STOP_SEQUENCES,
        },
    }
    if schema:
        body['format'] = schema

    try:
        response = requests.post(
            f'{_ollama_host()}/api/chat', json=body, timeout=OLLAMA_TIMEOUT
        )
        if response.status_code != 200:
            logger.warning('ollama -> %s %s', response.status_code, response.text[:200])
            return None
        return (response.json().get('message', {}).get('content') or '').strip() or None
    except (requests.RequestException, ValueError, KeyError) as exc:
        logger.warning('ollama request failed: %s', exc)
        return None


def _call_groq(prompt: str, system: str, temperature: float, max_tokens: int, heavy: bool) -> str | None:
    """Failover provider: hosted, keyed, used only when Ollama is down."""
    keys = _groq_keys()
    if not keys:
        return None

    model = _env('GROQ_MODEL_HEAVY', 'openai/gpt-oss-120b') if heavy else _env('GROQ_MODEL', 'openai/gpt-oss-20b')
    messages = ([{'role': 'system', 'content': system}] if system else []) + [
        {'role': 'user', 'content': prompt}
    ]

    for key in keys:
        try:
            response = requests.post(
                GROQ_URL,
                headers={'Authorization': f'Bearer {key}'},
                json={
                    'model': model,
                    'messages': messages,
                    'temperature': temperature,
                    'max_tokens': max_tokens,
                },
                timeout=TIMEOUT_SECONDS,
            )
            if response.status_code != 200:
                logger.warning('groq %s -> %s %s', model, response.status_code, response.text[:200])
                continue

            message = response.json()['choices'][0]['message']
            # gpt-oss models return chain-of-thought in `reasoning` alongside the
            # answer in `content`. Only `content` is ever shown to a user.
            text = (message.get('content') or '').strip()
            if text:
                return text
        except requests.RequestException as exc:
            logger.warning('groq request failed: %s', exc)

    return None


def _call_gemini(prompt: str, system: str, temperature: float, max_tokens: int) -> str | None:
    """Last failover."""
    key = _env('GEMINI_API_KEY')
    if not key:
        return None

    model = _env('GEMINI_MODEL', 'gemini-3.5-flash-lite')
    contents = []
    if system:
        contents += [
            {'role': 'user', 'parts': [{'text': system}]},
            {'role': 'model', 'parts': [{'text': 'Understood.'}]},
        ]
    contents.append({'role': 'user', 'parts': [{'text': prompt}]})

    try:
        response = requests.post(
            f'{GEMINI_URL.format(model=model)}?key={key}',
            json={
                'contents': contents,
                'generationConfig': {'temperature': temperature, 'maxOutputTokens': max_tokens},
            },
            timeout=TIMEOUT_SECONDS,
        )
        if response.status_code != 200:
            logger.warning('gemini %s -> %s %s', model, response.status_code, response.text[:200])
            return None

        parts = response.json()['candidates'][0]['content']['parts']
        return (parts[0].get('text') or '').strip() or None
    except (requests.RequestException, KeyError, IndexError) as exc:
        logger.warning('gemini request failed: %s', exc)
        return None


# --------------------------------------------------------------------------- #
# Health                                                                       #
# --------------------------------------------------------------------------- #

def ollama_ready() -> bool:
    """True when Ollama is up and the configured model is pulled."""
    try:
        response = requests.get(f'{_ollama_host()}/api/tags', timeout=3)
        names = {m['name'] for m in response.json().get('models', [])}
    except (requests.RequestException, ValueError, KeyError):
        return False

    wanted = _ollama_model()
    # `qwen2.5:0.5b-instruct` and a bare `qwen2.5:0.5b` are the same weights.
    return any(name == wanted or name.startswith(wanted.split(':')[0] + ':') for name in names)


def is_configured() -> bool:
    """True when at least one provider can answer."""
    return bool(ollama_ready() or _groq_keys() or _env('GEMINI_API_KEY'))


def warm() -> None:
    """Load the model into memory so the first real request is not the slow one.

    Called at startup. A cold generate costs about 25 seconds; every call after
    it costs under one, and ``keep_alive`` holds that for half an hour.
    """
    try:
        requests.post(
            f'{_ollama_host()}/api/generate',
            json={'model': _ollama_model(), 'prompt': 'ok', 'stream': False,
                  'keep_alive': KEEP_ALIVE, 'options': {'num_predict': 1}},
            timeout=OLLAMA_TIMEOUT,
        )
        logger.info('ollama warm: %s', _ollama_model())
    except requests.RequestException as exc:
        logger.info('ollama not warmed (%s); hosted providers will be used', exc)


def status() -> dict:
    """What the UI shows when it says where an answer came from."""
    local = ollama_ready()
    return {
        'available': bool(local or _groq_keys() or _env('GEMINI_API_KEY')),
        'local': local,
        'model': _ollama_model() if local else (_env('GROQ_MODEL') or 'hosted'),
        'private': local,
    }


# --------------------------------------------------------------------------- #
# Public API                                                                   #
# --------------------------------------------------------------------------- #

def complete(
    prompt: str,
    *,
    system: str = '',
    temperature: float = 0.6,
    max_tokens: int = 700,
    heavy: bool = False,
    cache_key: str | None = None,
    facts: dict | list | None = None,
    sentences: int = 0,
) -> str:
    """Return one completion, tidied and checked.

    :param facts: everything the answer is allowed to assert numerically. When
        given, a reply containing a figure that is not derivable from these is
        rejected and retried once at a lower temperature. This is the guard that
        makes a 0.5B model safe to put in front of somebody's savings.
    :param sentences: trim to at most this many sentences. The small model
        ignores "answer in 2 sentences", so the limit is enforced here instead.
    :param heavy: use the larger model where one exists. Locally there is only
        one model, so this only widens the token budget.
    :param cache_key: enables caching. Pass a key that captures everything the
        answer depends on; omit it for anything conversational.
    :raises NoProviderAvailable: when no provider answered.
    """
    if cache_key:
        full_key = f'llm:{hashlib.sha256(f"{cache_key}|{prompt}".encode()).hexdigest()[:32]}'
        hit = cache.get(full_key)
        if hit:
            return hit

    text = _generate(prompt, system, temperature, max_tokens, heavy, facts, sentences)

    if text is None:
        raise NoProviderAvailable('No LLM provider returned a response.')

    if cache_key:
        cache.set(full_key, text, CACHE_TTL)
    return text


def _generate(prompt, system, temperature, max_tokens, heavy, facts, sentences) -> str | None:
    """One completion through the provider chain, with a single grounded retry."""
    for attempt in range(2):
        raw = (
            _call_ollama(prompt, system, temperature if attempt == 0 else 0.1, max_tokens)
            or _call_groq(prompt, system, temperature, max_tokens, heavy)
            or _call_gemini(prompt, system, temperature, max_tokens)
        )
        if raw is None:
            return None

        text = guard.tidy(raw, sentences=sentences)
        if not text:
            continue

        if guard.drifted(text):
            logger.warning('reply drifted out of context (attempt %s): %s', attempt + 1, text[:160])
            continue

        if facts is None or guard.grounded(text, facts):
            return text

        logger.warning('ungrounded reply rejected (attempt %s): %s', attempt + 1, text[:160])

    # Both attempts invented figures. Saying nothing beats saying a wrong number
    # about somebody's money.
    return None


def complete_json(
    prompt: str,
    *,
    system: str = '',
    schema: dict | None = None,
    schema_hint: str = '',
    facts: dict | list | None = None,
    **kwargs,
) -> dict:
    """Return one completion parsed as JSON.

    With ``schema``, Ollama constrains decoding so the output cannot be invalid.
    Without it — or on a hosted failover — the first balanced object is extracted,
    because models wrap JSON in prose often enough that asking nicely is not a
    strategy.

    ``facts`` grounds the *text inside* the structure, which a schema cannot.
    Constrained decoding guarantees a well-formed object and says nothing about
    whether its strings are true: asked to assess a goal of Rs 25,00,000 over
    15.8 years on Rs 90,000 a month, the model returned perfectly valid JSON
    describing "$25 million", "15 months" and "60% of income ($48,000)". Every
    field was the right type and every number was invented.

    :raises NoProviderAvailable: when no provider answered.
    :raises ValueError: when the response contained no parsable object, or every
        attempt invented figures.
    """
    kwargs.pop('sentences', None)
    temperature = kwargs.pop('temperature', 0.2)
    max_tokens = kwargs.pop('max_tokens', 700)
    heavy = kwargs.pop('heavy', False)
    cache_key = kwargs.pop('cache_key', None)

    if cache_key:
        full_key = f'llm:json:{hashlib.sha256(f"{cache_key}|{prompt}".encode()).hexdigest()[:32]}'
        hit = cache.get(full_key)
        if hit:
            return json.loads(hit)

    instruction = 'Respond with a single JSON object and nothing else.'
    if schema_hint:
        instruction += f' Use exactly these keys: {schema_hint}.'
    full_system = f'{system}\n{instruction}'.strip()

    payload = None
    for attempt in range(2):
        raw = (
            _call_ollama(prompt, full_system, temperature if attempt == 0 else 0.1,
                         max_tokens, schema=schema)
            or _call_groq(prompt, full_system, temperature, max_tokens, heavy)
            or _call_gemini(prompt, full_system, temperature, max_tokens)
        )
        if raw is None:
            raise NoProviderAvailable('No LLM provider returned a response.')

        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if not match:
            continue

        try:
            candidate = json.loads(match.group(0))
        except json.JSONDecodeError:
            continue

        candidate = guard.tidy_payload(candidate)
        if facts is None or guard.grounded_payload(candidate, facts):
            payload = candidate
            break

        logger.warning('ungrounded JSON rejected (attempt %s)', attempt + 1)

    if payload is None:
        raise ValueError('No grounded JSON object in the model response.')

    if cache_key:
        cache.set(full_key, json.dumps(payload), CACHE_TTL)
    return payload
