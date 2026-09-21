"""
Tests for content search and the glossary.

Retrieval decides what the model is allowed to say, so a regression here is not
a search-quality nuisance — it is the difference between an answer quoting the
course and an answer the model made up.
"""

from django.test import SimpleTestCase

from ai import glossary, retrieve


class TokenTests(SimpleTestCase):
    def test_plurals_fold_to_the_singular(self):
        self.assertEqual(retrieve._tokens('funds'), ['fund'])

    def test_ing_folds_to_the_stem(self):
        """Without this, "what is compounding?" never reaches the passage that
        defines compound interest, and the model — left with three passages
        about SIPs — answered that compounding is "new money entering the
        market continuously"."""
        self.assertEqual(retrieve._tokens('compounding'), ['compound'])

    def test_a_double_s_is_not_a_plural(self):
        self.assertEqual(retrieve._tokens('loss'), ['loss'])

    def test_stopwords_are_dropped(self):
        self.assertEqual(retrieve._tokens('what is the'), [])

    def test_a_short_word_keeps_its_ending(self):
        """Stripping to a two-letter stem matches everything and means nothing."""
        self.assertEqual(retrieve._tokens('fees'), ['fees'])


class SearchTests(SimpleTestCase):
    def test_a_question_finds_its_course(self):
        hits = retrieve.search('what is a credit score', limit=3)
        self.assertTrue(hits)
        self.assertIn('debt-credit', {hit['course_id'] for hit in hits})

    def test_nonsense_finds_nothing(self):
        self.assertEqual(retrieve.search('qwertyuiop zxcvbnm'), [])

    def test_an_empty_query_finds_nothing(self):
        self.assertEqual(retrieve.search('   '), [])

    def test_results_carry_a_module_to_link_to(self):
        hits = retrieve.search('what is an index fund', limit=1)
        self.assertTrue(hits[0]['course_id'])
        self.assertTrue(hits[0]['module_id'])

    def test_the_context_block_respects_its_budget(self):
        hits = retrieve.search('emergency fund', limit=3)
        self.assertLessEqual(len(retrieve.context_block(hits, budget=200)), 400)


class DirectAnswerTests(SimpleTestCase):
    def test_the_authored_question_is_matched(self):
        found = retrieve.direct_answer('Is a SIP better than a lump-sum investment?')
        self.assertIsNotNone(found)
        self.assertIn('SIP', found['title'])

    def test_a_near_miss_is_refused(self):
        """"How big should my emergency fund be?" shares two words of three with
        "When should I use my emergency fund?". On a plain overlap both score
        the same and the wrong answer is served with confidence; the words that
        carry the question are the rare ones."""
        self.assertIsNone(retrieve.direct_answer('How big should my emergency fund be?'))

    def test_nonsense_matches_nothing(self):
        self.assertIsNone(retrieve.direct_answer('how do i cook pasta'))


class GlossaryTests(SimpleTestCase):
    def test_a_term_is_found(self):
        self.assertEqual(glossary.look_up('index fund')['term'], 'index fund')

    def test_a_question_resolves_to_its_term(self):
        self.assertEqual(glossary.look_up('What is compounding?')['term'], 'compounding')

    def test_an_alias_resolves(self):
        self.assertEqual(glossary.look_up('cibil')['term'], 'credit score')

    def test_an_unknown_term_returns_nothing(self):
        self.assertIsNone(glossary.look_up('quantum arbitrage swap'))

    def test_every_entry_has_a_definition_and_an_example(self):
        for term, entry in glossary.TERMS.items():
            self.assertTrue(entry['definition'].strip(), f'{term} has no definition')
            self.assertTrue(entry['example'].strip(), f'{term} has no example')

    def test_no_entry_quotes_a_foreign_currency(self):
        from ai import guard

        for term, entry in glossary.TERMS.items():
            self.assertFalse(
                guard.drifted(f'{entry["definition"]} {entry["example"]}'),
                f'{term} refers to another financial system',
            )

    def test_a_question_about_a_term_is_recognised(self):
        """The glossary answers "how big should my emergency fund be?" exactly.
        Left to the model, that question produced "at least twice your monthly
        income" and a reference to a Federal Reserve calculator."""
        found = glossary.asked_about('How big should my emergency fund be?')
        self.assertIsNotNone(found)
        self.assertEqual(found['term'], 'emergency fund')

    def test_a_question_about_an_event_is_not_a_definition_request(self):
        """Mentioning a term is not asking what it means."""
        self.assertIsNone(glossary.asked_about('Why did my index fund drop 10% this week?'))

    def test_strict_lookup_ignores_a_term_buried_in_a_question(self):
        self.assertIsNone(glossary.look_up('why did my index fund drop', fuzzy=False))
