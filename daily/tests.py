"""
Tests for the daily loop.

The puzzle must be identical for everyone on a given day — that is what makes a
shared score meaningful — and the review scheduler must actually space cards out.
"""

from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from daily import puzzles
from daily.models import PuzzleKind, ReviewCard


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
