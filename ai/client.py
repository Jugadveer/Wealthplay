"""
The single LLM entry point for the whole app.

Why this exists
---------------
Every AI surface used to call a provider directly, each with its own key
handling, its own prompt, and its own silent ``except: pass``. When both
configured models were retired upstream -- Gemini's ``gemini-2.0-flash-lite``
and Groq's ``llama-3.1-8b-instant`` both started returning 404 -- every one of
those surfaces quietly fell through to a hardcoded template. The UI kept saying
"AI" while serving string interpolation, and nothing logged a warning.

The design that prevents a repeat:

* One client, one place to change a model id.
* Providers are tried in order and the first success wins, so one dead provider
  degrades rather than breaks.
* When no provider answers, :func:`complete` raises. Callers decide what to show.
  Nothing here invents prose and passes it off as a model response.
* Identical prompts are cached, because the same explanation regenerated on
  every page view is latency and quota spent for no benefit.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re

import requests
from django.core.cache import cache

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 25
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


# --------------------------------------------------------------------------- #
# Providers                                                                    #
# --------------------------------------------------------------------------- #

def _call_groq(prompt: str, system: str, temperature: float, max_tokens: int, heavy: bool) -> str | None:
    """Primary provider: free tier, sub-second responses."""
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
    """Failover provider."""
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
# Public API                                                                   #
# --------------------------------------------------------------------------- #

def is_configured() -> bool:
    """True when at least one provider has a key."""
    return bool(_groq_keys() or _env('GEMINI_API_KEY'))


def complete(
    prompt: str,
    *,
    system: str = '',
    temperature: float = 0.6,
    max_tokens: int = 700,
    heavy: bool = False,
    cache_key: str | None = None,
) -> str:
    """Return one completion.

    :param heavy: use the larger model. Worth it for multi-step reasoning,
        wasteful for a one-line explanation.
    :param cache_key: enables caching. Pass a key that captures everything the
        answer depends on; omit it for anything user-specific and conversational.
    :raises NoProviderAvailable: when no provider answered.
    """
    if cache_key:
        full_key = f'llm:{hashlib.sha256(f"{cache_key}|{prompt}".encode()).hexdigest()[:32]}'
        hit = cache.get(full_key)
        if hit:
            return hit

    text = _call_groq(prompt, system, temperature, max_tokens, heavy)
    if text is None:
        text = _call_gemini(prompt, system, temperature, max_tokens)

    if text is None:
        raise NoProviderAvailable('No LLM provider returned a response.')

    if cache_key:
        cache.set(full_key, text, CACHE_TTL)
    return text


def complete_json(prompt: str, *, system: str = '', schema_hint: str = '', **kwargs) -> dict:
    """Return one completion parsed as JSON.

    Models wrap JSON in prose or fences often enough that extracting the first
    balanced object is more reliable than asking nicely and hoping.

    :raises NoProviderAvailable: when no provider answered.
    :raises ValueError: when the response contained no parsable object.
    """
    instruction = 'Respond with a single JSON object and nothing else.'
    if schema_hint:
        instruction += f' Use exactly these keys: {schema_hint}.'

    raw = complete(
        prompt,
        system=f'{system}\n{instruction}'.strip(),
        temperature=kwargs.pop('temperature', 0.2),
        **kwargs,
    )

    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if not match:
        raise ValueError(f'No JSON object in model response: {raw[:200]}')
    return json.loads(match.group(0))
