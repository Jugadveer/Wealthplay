"""
Tests for the daily loop.

The puzzle must be identical for everyone on a given day — that is what makes a
shared score meaningful — and the review scheduler must actually space cards out.
"""

from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from daily import games, puzzles
from daily.models import PuzzleKind, ReviewCard
from daily.words import LEDGER_WORDS


class SeedingTests(TestCase):
    def test_same_day_gives_the_same_puzzle(self):
        day = date(2026, 3, 14)
        first = puzzles.seeded_random(day, PuzzleKind.TICKER).random()
        second = puzzles.seeded_random(day, PuzzleKind.TICKER).random()
        self.assertEqual(first, second)

    def test_different_days_differ(self):
        a = puzzles.seeded_random(date(2026, 3, 14), PuzzleKind.TICKER).random()
        b = puzzles.seeded_random(date(2026, 3, 15), PuzzleKind.TICKER).random()
        self.assertNotEqual(a, b)

    def test_puzzle_kinds_do_not_collide(self):
        day = date(2026, 3, 14)
        ticker = puzzles.seeded_random(day, PuzzleKind.TICKER).random()
        estimate = puzzles.seeded_random(day, PuzzleKind.ESTIMATE).random()
        self.assertNotEqual(ticker, estimate)


class ScoringTests(TestCase):
    def test_fewer_guesses_score_higher(self):
        scores = [puzzles.score_ticker(n, True) for n in range(1, 6)]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertTrue(all(score > 0 for score in scores))

    def test_an_unsolved_board_scores_nothing(self):
        self.assertEqual(puzzles.score_ticker(5, False), 0)

    def test_estimates_are_banded_by_closeness(self):
        self.assertEqual(puzzles.score_estimate(100, 100)[1], 'spot on')
        self.assertEqual(puzzles.score_estimate(105, 100)[1], 'very close')
        self.assertEqual(puzzles.score_estimate(120, 100)[1], 'close')
        self.assertEqual(puzzles.score_estimate(500, 100)[1], 'way off')

    def test_being_under_or_over_scores_the_same(self):
        self.assertEqual(puzzles.score_estimate(90, 100), puzzles.score_estimate(110, 100))

    def test_silhouette_normalises_to_shape_only(self):
        """The shape is the clue; the price level must not leak through it."""
        cheap = puzzles._silhouette([i * 1.0 for i in range(100)])
        pricey = puzzles._silhouette([i * 1000.0 for i in range(100)])
        self.assertEqual(cheap, pricey)
        self.assertTrue(all(0 <= value <= 1 for value in cheap))


class ReviewSchedulingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('student', password='x')
        self.card = ReviewCard.objects.create(
            user=self.user,
            course_id='investing-basics',
            module_id='m1',
            question_id='investing-basics:m1:1',
            question='?',
            options=['a', 'b', 'c', 'd'],
            correct_index=0,
        )

    def test_intervals_lengthen_while_recall_holds(self):
        today = date(2026, 1, 1)
        intervals = []
        for step in range(4):
            self.card.review(True, today + timedelta(days=step))
            intervals.append(self.card.interval_days)

        self.assertEqual(intervals[:2], [1, 4])
        self.assertGreater(intervals[2], intervals[1])
        self.assertGreater(intervals[3], intervals[2])

    def test_a_miss_brings_the_card_back_tomorrow(self):
        self.card.review(True)
        self.card.review(True)
        self.card.review(False)

        self.assertEqual(self.card.interval_days, 1)
        self.assertEqual(self.card.repetitions, 0)
        self.assertEqual(self.card.lapses, 1)

    def test_ease_never_falls_below_the_floor(self):
        for _ in range(20):
            self.card.review(False)
        self.assertGreaterEqual(self.card.ease, ReviewCard.MIN_EASE)

    def test_a_correct_card_is_not_due_again_today(self):
        today = date(2026, 1, 1)
        self.card.review(True, today)
        self.assertGreater(self.card.due_on, today)

class RepetitionTests(TestCase):
    """Nothing in the daily set may repeat before the whole list has been used."""

    def test_a_pick_cycles_before_it_repeats(self):
        """Regression: rng.choice drew independently, so tickers repeated in a week."""
        items = list(range(10))
        picks = [puzzles.daily_pick(items, date(2026, 1, 1) + timedelta(days=offset), 'x')[0]
                 for offset in range(10)]
        self.assertEqual(sorted(picks), items)

    def test_a_pick_is_the_same_for_everyone(self):
        day = date(2026, 5, 4)
        first = puzzles.daily_pick(list(range(20)), day, 'ticker')
        second = puzzles.daily_pick(list(range(20)), day, 'ticker')
        self.assertEqual(first, second)

    def test_different_games_pick_differently_on_the_same_day(self):
        day = date(2026, 5, 4)
        self.assertNotEqual(
            puzzles.daily_pick(list(range(30)), day, 'ticker'),
            puzzles.daily_pick(list(range(30)), day, 'ledger'),
        )


class LedgerTests(TestCase):
    def test_marks_exact_letters_first(self):
        self.assertEqual(
            games.mark_guess('STOCK', 'STOCK'),
            ['hit', 'hit', 'hit', 'hit', 'hit'],
        )

    def test_a_repeated_letter_is_not_double_credited(self):
        """SPLIT against STOCK has one T, so only one tile may be marked for it."""
        marks = games.mark_guess('SPLIT', 'STOCK')
        self.assertEqual(marks[0], 'hit')
        self.assertEqual(marks.count('near'), 1)

    def test_a_letter_not_in_the_word_misses(self):
        self.assertEqual(games.mark_guess('ZZZZZ', 'STOCK'), ['miss'] * 5)

    def test_score_rewards_fewer_guesses(self):
        self.assertGreater(games.score_ledger(1, True), games.score_ledger(5, True))
        self.assertEqual(games.score_ledger(6, False), 0)

    def test_every_word_is_five_letters_with_a_definition(self):
        for word, meaning in LEDGER_WORDS:
            with self.subTest(word=word):
                self.assertEqual(len(word), 5)
                self.assertTrue(word.isalpha() and word.isupper())
                self.assertTrue(meaning.strip())

    def test_no_duplicate_words(self):
        words = [word for word, _ in LEDGER_WORDS]
        self.assertEqual(len(words), len(set(words)))


class RankTests(TestCase):
    def test_a_perfect_order_scores_every_pair(self):
        points, concordant, pairs = games.score_rank(['A', 'B', 'C', 'D'], ['A', 'B', 'C', 'D'])
        self.assertEqual((concordant, pairs), (6, 6))
        self.assertEqual(points, 50)

    def test_a_reversed_order_scores_nothing(self):
        points, concordant, _ = games.score_rank(['D', 'C', 'B', 'A'], ['A', 'B', 'C', 'D'])
        self.assertEqual((points, concordant), (0, 0))

    def test_one_swap_still_earns_most_of_the_marks(self):
        """Knowing the winner and the loser is most of the understanding."""
        points, concordant, pairs = games.score_rank(['A', 'C', 'B', 'D'], ['A', 'B', 'C', 'D'])
        self.assertEqual((concordant, pairs), (5, 6))
        self.assertGreater(points, 40)
