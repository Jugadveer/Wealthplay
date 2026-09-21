"""
Tests for the LLM client.

The point of these is the failure path. Both configured models were retired
upstream at once and every AI surface silently fell back to a hardcoded
template, with nothing logged. The client must now fail loudly and degrade
predictably.
"""

from unittest.mock import Mock, patch

import requests
from django.core.cache import cache
from django.test import TestCase, override_settings

from ai import client


def groq_response(content, status=200):
    response = Mock(status_code=status)
    response.json.return_value = {
        'choices': [{'message': {'content': content, 'reasoning': 'internal chain of thought'}}]
    }
    response.text = content
    return response


@override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
class CompleteTests(TestCase):
    def setUp(self):
        cache.clear()

    @patch.dict('os.environ', {'GROQ_API_KEY': 'key-1', 'GEMINI_API_KEY': ''})
    @patch('ai.client.requests.post')
    def test_returns_content_and_ignores_reasoning(self, post):
        """gpt-oss models return chain-of-thought; only content reaches a user."""
        post.return_value = groq_response('An index fund tracks a market.')

        answer = client.complete('what is an index fund?')

        self.assertEqual(answer, 'An index fund tracks a market.')
        self.assertNotIn('chain of thought', answer)

    @patch.dict('os.environ', {'GROQ_API_KEY': 'dead-key', 'GROQ_API_KEY_2': 'good-key', 'GEMINI_API_KEY': ''})
    @patch('ai.client.requests.post')
    def test_falls_over_to_the_second_key(self, post):
        post.side_effect = [groq_response('bad key', status=401), groq_response('worked')]
        self.assertEqual(client.complete('hello'), 'worked')
        self.assertEqual(post.call_count, 2)

    @patch.dict('os.environ', {'GROQ_API_KEY': 'key-1', 'GEMINI_API_KEY': ''})
    @patch('ai.client.requests.post')
    def test_a_retired_model_raises_rather_than_returning_a_template(self, post):
        """Regression: a 404 on a retired model became a silent canned answer."""
        post.return_value = groq_response('model not found', status=404)

        with self.assertRaises(client.NoProviderAvailable):
            client.complete('hello')

    @patch.dict('os.environ', {'GROQ_API_KEY': '', 'GROQ_API_KEY_2': '', 'GEMINI_API_KEY': ''})
    def test_no_keys_raises(self):
        self.assertFalse(client.is_configured())
        with self.assertRaises(client.NoProviderAvailable):
            client.complete('hello')

    @patch.dict('os.environ', {'GROQ_API_KEY': 'key-1', 'GEMINI_API_KEY': ''})
    @patch('ai.client.requests.post')
    def test_a_timeout_is_not_an_unhandled_error(self, post):
        post.side_effect = requests.Timeout('too slow')
        with self.assertRaises(client.NoProviderAvailable):
            client.complete('hello')

    @patch.dict('os.environ', {'GROQ_API_KEY': 'key-1', 'GEMINI_API_KEY': ''})
    @patch('ai.client.requests.post')
    def test_a_cache_key_prevents_a_second_call(self, post):
        post.return_value = groq_response('cached answer')

        first = client.complete('same prompt', cache_key='fixed')
        second = client.complete('same prompt', cache_key='fixed')

        self.assertEqual(first, second)
        self.assertEqual(post.call_count, 1)


@override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
class CompleteJsonTests(TestCase):
    def setUp(self):
        cache.clear()

    @patch.dict('os.environ', {'GROQ_API_KEY': 'key-1', 'GEMINI_API_KEY': ''})
    @patch('ai.client.requests.post')
    def test_extracts_json_from_a_fenced_block(self, post):
        post.return_value = groq_response('Sure!\n```json\n{"grade": "B"}\n```\nHope that helps.')
        self.assertEqual(client.complete_json('grade it'), {'grade': 'B'})

    @patch.dict('os.environ', {'GROQ_API_KEY': 'key-1', 'GEMINI_API_KEY': ''})
    @patch('ai.client.requests.post')
    def test_extracts_json_surrounded_by_prose(self, post):
        post.return_value = groq_response('Here you go: {"grade": "A"} — anything else?')
        self.assertEqual(client.complete_json('grade it'), {'grade': 'A'})

    @patch.dict('os.environ', {'GROQ_API_KEY': 'key-1', 'GEMINI_API_KEY': ''})
    @patch('ai.client.requests.post')
    def test_a_response_with_no_object_raises(self, post):
        post.return_value = groq_response('I would rather not.')
        with self.assertRaises(ValueError):
            client.complete_json('grade it')


@override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
class DegradationTests(TestCase):
    """Views must receive None, not an exception, when no provider answers."""

    def setUp(self):
        cache.clear()

    @patch.dict('os.environ', {'GROQ_API_KEY': '', 'GROQ_API_KEY_2': '', 'GEMINI_API_KEY': ''})
    def test_every_tutor_entry_point_degrades_to_none(self):
        from ai import tutor

        self.assertIsNone(
            tutor.answer_lesson_question('why?', module_title='Inflation', theory='Prices rise.')
        )
        self.assertIsNone(
            tutor.explain_wrong_answer('q', 'a', 'b', module_title='Inflation')
        )
        self.assertIsNone(
            tutor.review_portfolio(
                [{'symbol': 'AAPL', 'sector': 'Tech', 'quantity': 1, 'pnl_percent': 0, 'current_value': 100}],
                cash=0,
                pnl_percent=0,
            )
        )
        self.assertIsNone(tutor.weekly_recap({}))

    def test_a_review_of_nothing_returns_none_without_calling_a_model(self):
        from ai import tutor

        self.assertIsNone(tutor.review_portfolio([], cash=0, pnl_percent=0))
