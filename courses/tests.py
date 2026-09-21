"""
Tests for the content pipeline.

The course catalogue is parsed from hand-edited JSON on disk, so these guard the
two things that actually broke: generation artifacts reaching the screen, and
the catalogue being re-read on every request.
"""

from django.test import TestCase

from courses import content


class CleanTests(TestCase):
    def test_strips_image_placeholders(self):
        """Regression: "[Image of an inflation chart...]" shipped as body copy."""
        self.assertEqual(
            content.clean('Inflation erodes savings. [Image of inflation chart over 20 years]'),
            'Inflation erodes savings.',
        )

    def test_unwraps_latex_maths(self):
        self.assertEqual(content.clean(r'a $\text{₹}1,00,000$ limit'), 'a ₹1,00,000 limit')

    def test_unwraps_latex_whose_backslash_json_ate(self):
        """The source JSON wrote "\\text{", so JSON parsing left TAB + "ext{"."""
        self.assertEqual(content.clean('you owe \text{₹}5,000 today'), 'you owe ₹5,000 today')

    def test_keeps_markdown_emphasis_for_the_client(self):
        self.assertEqual(content.clean('due to **Inflation**'), 'due to **Inflation**')

    def test_handles_empty_input(self):
        self.assertEqual(content.clean(None), '')
        self.assertEqual(content.clean(''), '')


class SummaryTests(TestCase):
    """The catalogue blurb is the first thing a learner reads about a course."""

    def test_ends_on_a_sentence(self):
        """Regression: blurbs were a 180-character slice that stopped mid-word."""
        theory = 'A savings account holds cash you may need today. ' + 'It pays little. ' * 20
        self.assertTrue(content._summarise(theory, []).endswith('.'))

    def test_flattens_markdown_emphasis(self):
        """Regression: "**after-tax income**" rendered as literal asterisks."""
        self.assertEqual(
            content._summarise('Divide your **after-tax income** three ways.', []),
            'Divide your after-tax income three ways.',
        )

    def test_falls_back_to_a_question(self):
        self.assertEqual(
            content._summarise('', [{'question': 'What is an FD?', 'answer': 'A fixed deposit.'}]),
            'A fixed deposit.',
        )

    def test_every_course_blurb_is_readable(self):
        for course in content.catalogue():
            with self.subTest(course=course['id']):
                self.assertNotIn('*', course['summary'])
                self.assertTrue(course['summary'])


class CatalogueTests(TestCase):
    def test_catalogue_loads(self):
        courses = content.catalogue()
        self.assertGreater(len(courses), 0)
        self.assertTrue(all(course['modules'] for course in courses))

    def test_catalogue_is_cached(self):
        """Parsed once per process; it used to re-read ~96 files per request."""
        self.assertIs(content.catalogue(), content.catalogue())

    def test_no_artifacts_survive_anywhere(self):
        for course in content.catalogue():
            for module in course['modules']:
                blob = ' '.join(
                    [module['theory'], module['summary']]
                    + [q['question'] for q in module['mcqs']]
                    + [p['answer'] for p in module['qna']]
                )
                for artifact in ('[Image', 'ext{', '$', '\\'):
                    self.assertNotIn(artifact, blob, f'{course["id"]}/{module["id"]}')

    def test_cards_have_a_front_and_a_back(self):
        """Regression: cards rendered the answer face-up, so there was no recall."""
        module = content.get_module('investing-basics', 'm1')
        for card in module['cards']:
            self.assertTrue(card['prompt'])
            self.assertTrue(card['answer'])

    def test_questions_resolve_to_a_valid_index(self):
        for course in content.catalogue():
            for module in course['modules']:
                for question in module['mcqs']:
                    self.assertIn(question['correct_index'], range(len(question['options'])))

    def test_next_module_walks_a_course_and_stops(self):
        """Regression: lessons dead-ended with no way forward."""
        self.assertEqual(content.next_module('investing-basics', 'm1')['id'], 'm2')

        course = content.get_course('investing-basics')
        self.assertIsNone(content.next_module('investing-basics', course['modules'][-1]['id']))

    def test_unknown_ids_return_none(self):
        self.assertIsNone(content.get_course('no-such-course'))
        self.assertIsNone(content.get_module('investing-basics', 'no-such-module'))
