"""
Tests for the scenario bank and its loader.

The bank is hand-written data, and hand-written data is where the errors are: a
scenario with no good answer, a duplicate title that silently overwrites another,
an option typed as something the model does not accept.
"""

from django.core.management import call_command
from django.test import TestCase

from simulator.models import DecisionOption, Scenario
from simulator.scenario_bank import BANK


class ScenarioBankTests(TestCase):
    def test_the_bank_is_large_enough_to_not_repeat(self):
        """Four per run, so this is weeks of play before anything comes back."""
        self.assertGreaterEqual(len(BANK), 40)

    def test_titles_are_unique(self):
        """A duplicate title would silently overwrite the other on seeding."""
        titles = [case.title for case in BANK]
        self.assertEqual(len(titles), len(set(titles)))

    def test_every_case_has_three_options(self):
        for case in BANK:
            with self.subTest(case=case.title):
                self.assertEqual(len(case.options), 3)

    def test_every_case_has_a_clearly_best_answer(self):
        """A scenario where nothing scores well teaches nothing."""
        for case in BANK:
            with self.subTest(case=case.title):
                scores = [option.score for option in case.options]
                self.assertGreaterEqual(max(scores), 15)
                self.assertLess(min(scores), max(scores))

    def test_option_types_are_ones_the_model_accepts(self):
        allowed = {value for value, _ in DecisionOption.TYPE_CHOICES}
        for case in BANK:
            for option in case.options:
                with self.subTest(case=case.title, option=option.text):
                    self.assertIn(option.kind, allowed)

    def test_every_option_explains_itself(self):
        """The explanation is the product; an option without one is a dead end."""
        for case in BANK:
            for option in case.options:
                with self.subTest(case=case.title, option=option.text):
                    self.assertGreater(len(option.why), 40)
                    self.assertTrue(option.mentor.strip())


class SeedCommandTests(TestCase):
    def test_seeding_twice_does_not_duplicate(self):
        call_command('seed_scenarios', verbosity=0)
        first = Scenario.objects.count()
        options = DecisionOption.objects.count()

        call_command('seed_scenarios', verbosity=0)

        self.assertEqual(Scenario.objects.count(), first)
        self.assertEqual(DecisionOption.objects.count(), options)

    def test_seeding_loads_the_whole_bank(self):
        call_command('seed_scenarios', verbosity=0)
        self.assertEqual(Scenario.objects.count(), len(BANK))
        self.assertEqual(DecisionOption.objects.count(), len(BANK) * 3)
