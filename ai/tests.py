"""
Tests for the LLM client.

The point of these is the failure path. Both configured models were retired
upstream at once and every AI surface silently fell back to a hardcoded
template, with nothing logged. The client must fail loudly and degrade
predictably.

None of them require Ollama to be running. The local model is the primary
provider in production, and a test suite that only passes on a machine with a
model loaded is not a test suite — so ``_call_ollama`` is patched out wherever
the hosted chain is under test, and exercised directly with a mocked transport
where it is the subject.
"""

from unittest.mock import Mock, patch

import requests
from django.core.cache import cache
from django.test import TestCase, override_settings

from ai import client

LOCMEM = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}


def groq_response(content, status=200):
    response = Mock(status_code=status)
    response.json.return_value = {
        'choices': [{'message': {'content': content, 'reasoning': 'internal chain of thought'}}]
    }
    response.text = content
    return response


def ollama_response(content, status=200):
    response = Mock(status_code=status)
    response.json.return_value = {'message': {'role': 'assistant', 'content': content}}
    response.text = content
    return response


@override_settings(CACHES=LOCMEM)
class OllamaTests(TestCase):
    """The primary provider."""

    def setUp(self):
        cache.clear()

    @patch('ai.client.requests.post')
    def test_a_completion_comes_back_tidied(self, post):
        post.return_value = ollama_response('**Bold** answer.')
        self.assertEqual(client.complete('hello'), 'Bold answer.')

    @patch('ai.client.requests.post')
    def test_it_posts_to_the_chat_endpoint(self, post):
        """`/api/generate` makes an instruct model continue the prompt.

        That is how prompt scaffolding ended up inside answers, so the endpoint
        is part of the contract rather than an implementation detail.
        """
        post.return_value = ollama_response('Fine.')
        client.complete('hello', system='Be brief.')

        url, kwargs = post.call_args[0][0], post.call_args[1]
        self.assertTrue(url.endswith('/api/chat'))
        self.assertEqual(
            [message['role'] for message in kwargs['json']['messages']], ['system', 'user']
        )

    @patch('ai.client.requests.post')
    def test_the_model_is_kept_loaded(self, post):
        """A cold load costs 25 seconds. Paying it once is the whole point."""
        post.return_value = ollama_response('Fine.')
        client.complete('hello')
        self.assertEqual(post.call_args[1]['json']['keep_alive'], client.KEEP_ALIVE)

    @patch('ai.client.requests.post')
    def test_a_schema_is_sent_for_constrained_decoding(self, post):
        post.return_value = ollama_response('{"grade": "C"}')
        schema = {'type': 'object', 'properties': {'grade': {'type': 'string'}}}
        client.complete_json('grade it', schema=schema)
        self.assertEqual(post.call_args[1]['json']['format'], schema)

    @patch('ai.client.requests.post', side_effect=requests.ConnectionError('refused'))
    def test_ollama_being_down_is_not_an_unhandled_error(self, post):
        with self.assertRaises(client.NoProviderAvailable):
            client.complete('hello')


@override_settings(CACHES=LOCMEM)
@patch('ai.client._call_ollama', return_value=None)
class FailoverTests(TestCase):
    """What happens when the local model is not there."""

    def setUp(self):
        cache.clear()
        self.env = patch.dict(
            'os.environ', {'GROQ_API_KEY': 'key-one', 'GROQ_API_KEY_2': 'key-two'}
        )
        self.env.start()
        self.addCleanup(self.env.stop)

    @patch('ai.client.requests.post')
    def test_returns_content_and_ignores_reasoning(self, post, _ollama):
        post.return_value = groq_response('The answer.')
        self.assertEqual(client.complete('hello'), 'The answer.')

    @patch('ai.client.requests.post')
    def test_falls_over_to_the_second_key(self, post, _ollama):
        post.side_effect = [groq_response('rate limited', status=429), groq_response('The answer.')]
        self.assertEqual(client.complete('hello'), 'The answer.')

    @patch('ai.client.requests.post')
    def test_a_retired_model_raises_rather_than_returning_a_template(self, post, _ollama):
        post.return_value = groq_response('model not found', status=404)
        with self.assertRaises(client.NoProviderAvailable):
            client.complete('hello')

    @patch('ai.client.requests.post', side_effect=requests.Timeout('too slow'))
    def test_a_timeout_is_not_an_unhandled_error(self, post, _ollama):
        with self.assertRaises(client.NoProviderAvailable):
            client.complete('hello')

    @patch('ai.client.requests.post')
    def test_a_cache_key_prevents_a_second_call(self, post, _ollama):
        post.return_value = groq_response('Cached answer.')
        client.complete('hello', cache_key='same')
        client.complete('hello', cache_key='same')
        self.assertEqual(post.call_count, 1)


@override_settings(CACHES=LOCMEM)
class NoProviderTests(TestCase):
    def setUp(self):
        cache.clear()

    @patch('ai.client._call_ollama', return_value=None)
    def test_no_keys_and_no_local_model_raises(self, _ollama):
        with patch.dict('os.environ', {'GROQ_API_KEY': '', 'GROQ_API_KEY_2': '', 'GEMINI_API_KEY': ''}):
            with self.assertRaises(client.NoProviderAvailable):
                client.complete('hello')

    @patch('ai.client.requests.get', side_effect=requests.ConnectionError('refused'))
    def test_status_reports_no_local_model_when_ollama_is_down(self, _get):
        self.assertFalse(client.ollama_ready())


@override_settings(CACHES=LOCMEM)
@patch('ai.client._call_ollama')
class CompleteJsonTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_extracts_json_from_a_fenced_block(self, ollama):
        ollama.return_value = '```json\n{"a": 1}\n```'
        self.assertEqual(client.complete_json('hello'), {'a': 1})

    def test_extracts_json_surrounded_by_prose(self, ollama):
        ollama.return_value = 'Sure, here you go: {"a": 1} — hope that helps.'
        self.assertEqual(client.complete_json('hello'), {'a': 1})

    def test_a_response_with_no_object_raises(self, ollama):
        ollama.return_value = 'I would rather not.'
        with self.assertRaises(ValueError):
            client.complete_json('hello')

    def test_invented_figures_inside_valid_json_are_rejected(self, ollama):
        """A schema guarantees the shape of an answer, not its truth.

        This is the exact failure it was added for: perfectly valid JSON
        describing "$25 million" for a Rs 25,00,000 goal.
        """
        ollama.return_value = '{"note": "The target of $25 million is not feasible."}'
        with self.assertRaises(ValueError):
            client.complete_json('assess it', facts={'target': 2_500_000})

    def test_grounded_json_is_returned(self, ollama):
        ollama.return_value = '{"note": "The target of Rs 25,00,000 is reachable."}'
        self.assertIn('25,00,000', client.complete_json('assess it', facts={'target': 2_500_000})['note'])


@override_settings(CACHES=LOCMEM)
class DegradationTests(TestCase):
    """Nothing fabricates an analysis when no provider answers."""

    def setUp(self):
        cache.clear()

    @patch('ai.client._call_ollama', return_value=None)
    def test_every_tutor_entry_point_degrades_to_none(self, _ollama):
        from ai import coach, tutor

        with patch.dict('os.environ', {'GROQ_API_KEY': '', 'GROQ_API_KEY_2': '', 'GEMINI_API_KEY': ''}):
            self.assertIsNone(
                tutor.explain_wrong_answer('q', 'a', 'b', module_title='m')
            )
            self.assertIsNone(
                tutor.judge_prediction('TCS', called='up', actual='down',
                                       rationale='felt right', move_percent=-2.0)
            )
            self.assertIsNone(
                tutor.critique_trade('TCS', action='buy', quantity=1,
                                     rationale='momentum', weight_percent=10)
            )
            self.assertIsNone(tutor.weekly_recap({'modules': 1}))
            self.assertIsNone(tutor.generate_drill_questions('m', 'theory'))
            self.assertIsNone(
                tutor.assess_goal(description='a car', facts={'x': 1}, capacity={'level': 'low'})
            )
            self.assertIsNone(coach.daily_brief(name='A', stats={}))

    def test_a_hint_without_enough_history_never_calls_a_model(self):
        from ai import tutor

        with patch('ai.client._call_ollama') as ollama:
            self.assertIsNone(tutor.chart_hint('TCS', 'Tata', [{'close': 100}]))
            ollama.assert_not_called()

    def test_help_that_needs_no_model_still_works_without_one(self):
        """Page guidance and metric explanations are written, not generated.

        They were on the model until it told a user with Rs 24,000 of cash to
        save "$24000", and read a diversification score of 31 out of 100 as "an
        average return rate of about 31%".
        """
        from ai import coach

        with patch('ai.client._call_ollama') as ollama:
            self.assertTrue(coach.page_help('markets', facts={'holdings': 0}))
            self.assertTrue(coach.explain_number('Diversification score', 31))
            ollama.assert_not_called()
