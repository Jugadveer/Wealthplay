"""
Tests for the guard.

This is what stands between a half-billion-parameter model and somebody's
savings, so every case below is one the model actually produced against this
app's own prompts. If one of these regresses, a user sees a wrong number about
their own money.
"""

from django.test import SimpleTestCase

from ai import guard


class TidyTests(SimpleTestCase):
    def test_markdown_is_stripped(self):
        self.assertEqual(guard.tidy('**Bold** and `code`.'), 'Bold and code.')

    def test_headings_and_bullets_lose_their_markers_but_keep_their_text(self):
        cleaned = guard.tidy('### Why\n- spreads risk\n- lowers cost')
        self.assertNotIn('#', cleaned)
        self.assertNotIn('- ', cleaned)
        self.assertIn('spreads risk', cleaned)

    def test_stacked_preamble_is_removed(self):
        self.assertEqual(guard.tidy('Sure! Here is the answer: you should save.'), 'You should save.')

    def test_a_sentence_cut_off_mid_word_is_dropped(self):
        """The token budget runs out mid-word and the fragment is not an answer."""
        self.assertEqual(guard.tidy('Done. And your sta'), 'Done.')

    def test_an_abbreviation_is_not_mistaken_for_the_end_of_a_sentence(self):
        """Trimming at the last full stop here would leave the user reading "Rs."."""
        self.assertEqual(guard.tidy('Rs. 5,000 is fine'), 'Rs. 5,000 is fine')

    def test_the_sentence_cap_is_enforced(self):
        self.assertEqual(guard.tidy('One. Two. Three. Four.', sentences=2), 'One. Two.')

    def test_a_list_dump_after_the_prose_is_discarded(self):
        """Asked for two sentences on emergency funds, it answered in two and
        then appended headed sections on debt, insurance and school fees."""
        answer = (
            'Keep three to six months of expenses.\n\n'
            'High-interest Debt:\nPay it off first\n\n'
            'Insurance:\nPrioritise cover'
        )
        self.assertEqual(guard.tidy(answer, sentences=2), 'Keep three to six months of expenses.')

    def test_prompt_scaffolding_is_removed(self):
        answer = 'Compounding is interest on interest. Learner asks: What is compounding?'
        self.assertEqual(guard.tidy(answer), 'Compounding is interest on interest.')

    def test_an_enum_value_is_not_capitalised(self):
        """Capitalising every string turned "can_take_risk" into "Can_take_risk"
        and failed the schema the model had just satisfied."""
        self.assertEqual(guard.tidy('can_take_risk'), 'can_take_risk')

    def test_prose_is_capitalised(self):
        self.assertEqual(guard.tidy('you should save.'), 'You should save.')

    def test_empty_input_is_handled(self):
        self.assertEqual(guard.tidy(''), '')


class GroundingTests(SimpleTestCase):
    FACTS = {'monthly': 12_400, 'equity_percent': 45, 'years': 15.8, 'surplus': 30_000}

    def test_supplied_figures_pass(self):
        self.assertTrue(guard.grounded(
            'Put Rs 12,400 a month into 45% equity over 15.8 years.', self.FACTS))

    def test_an_invented_amount_is_rejected(self):
        self.assertFalse(guard.grounded('You need Rs 50,000 a month.', self.FACTS))

    def test_an_invented_rate_is_rejected(self):
        self.assertFalse(guard.grounded('Your rate is 12%.', self.FACTS))

    def test_prose_counting_is_not_treated_as_a_claim(self):
        """Rejecting "two things stand out" would reject almost everything."""
        self.assertTrue(guard.grounded('Two things stand out and 3 steps remain.', self.FACTS))

    def test_a_year_is_not_an_amount(self):
        self.assertTrue(guard.grounded('In 2026 you will be fine.', self.FACTS))

    def test_rounding_a_supplied_figure_is_allowed(self):
        self.assertTrue(guard.grounded('About Rs 12,400 a month.', {'monthly': 12_399.6}))

    def test_a_wrong_time_unit_is_rejected(self):
        """"15 months" for a horizon of 15.8 years is the same class of error as
        a wrong rupee figure, and a bare 15 would otherwise pass as prose."""
        self.assertFalse(guard.grounded('Within a short period of 15 months.',
                                        {'years_away': 15.8, 'months_away': 190}))

    def test_the_right_time_unit_passes(self):
        self.assertTrue(guard.grounded('Over 190 months.', {'years_away': 15.8, 'months_away': 190}))

    def test_a_foreign_currency_is_rejected_whatever_the_number(self):
        self.assertFalse(guard.grounded('Your income is $90,000 per month.',
                                        {'monthly_income': 90_000}))

    def test_figures_inside_a_structure_are_checked(self):
        """A JSON schema guarantees shape, not truth."""
        payload = {'headline': 'Fine', 'risks': ['The target of $25 million is not feasible.']}
        self.assertFalse(guard.grounded_payload(payload, {'target': 2_500_000}))

    def test_a_grounded_structure_passes(self):
        payload = {'headline': 'Rs 25,00,000 is reachable.', 'risks': ['Rs 90,000 covers it.']}
        self.assertTrue(guard.grounded_payload(payload, {'target': 2_500_000, 'income': 90_000}))


class DriftTests(SimpleTestCase):
    """Answers that wandered into another country's financial system."""

    def test_a_us_regulator_is_caught(self):
        self.assertTrue(guard.drifted(
            'Use the calculator provided by the Federal Reserve Bank of New York.'))

    def test_a_us_index_is_caught(self):
        self.assertTrue(guard.drifted('Funds that track the S&P 500 are cheapest.'))

    def test_an_indian_answer_is_not_flagged(self):
        self.assertFalse(guard.drifted(
            'A Nifty 50 index fund charges about 0.2% a year against 1.8%.'))


class SentenceTests(SimpleTestCase):
    def test_sentences_are_split(self):
        self.assertEqual(len(guard.split_sentences('One. Two. Three.')), 3)

    def test_an_abbreviation_does_not_split_a_sentence(self):
        self.assertEqual(len(guard.split_sentences('You need Rs. 5,000 a month. That is fine.')), 2)

    def test_a_decimal_does_not_split_a_sentence(self):
        self.assertEqual(len(guard.split_sentences('It moved 1.5% today.')), 1)
