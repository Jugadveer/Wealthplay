"""
Tests for the simulated market.

The practice stocks used to sit still: nothing ran the nightly job, so prices
never changed and every position showed +0.00%. These pin the two properties
that fixed it — determinism, so prices can catch up lazily on read, and a shared
market factor, so concentration is actually risky.
"""

from datetime import date, timedelta

from django.test import TestCase

from users.models import CustomStock
from users.portfolio import simulation


def _stock(**overrides) -> CustomStock:
    defaults = {
        'symbol': 'TESTCO',
        'name': 'Test Company',
        'base_price': 100,
        'current_price': 100,
        'stock_type': 'stable',
        'sector': 'Technology',
        'volatility': 0.02,
    }
    return CustomStock.objects.create(**{**defaults, **overrides})


class DeterminismTests(TestCase):
    """The same day must produce the same price, whoever computes it."""

    def test_a_day_return_is_reproducible(self):
        stock = _stock()
        day = date(2026, 4, 15)
        self.assertEqual(
            simulation.daily_return(stock, day, 100.0),
            simulation.daily_return(stock, day, 100.0),
        )

    def test_different_days_differ(self):
        stock = _stock()
        self.assertNotEqual(
            simulation.daily_return(stock, date(2026, 4, 15), 100.0),
            simulation.daily_return(stock, date(2026, 4, 16), 100.0),
        )

    def test_two_stocks_differ_on_the_same_day(self):
        a, b = _stock(symbol='AAA'), _stock(symbol='BBB')
        day = date(2026, 4, 15)
        self.assertNotEqual(
            simulation.daily_return(a, day, 100.0),
            simulation.daily_return(b, day, 100.0),
        )

    def test_catching_up_lazily_matches_stepping_daily(self):
        """Advancing on read must produce the series a nightly job would have.

        This is what lets prices catch up when a quote is asked for, on a machine
        where no scheduler is running, without the path depending on who looked.
        """
        stock = _stock(symbol='LAZY')
        start, end = date(2026, 4, 1), date(2026, 4, 11)

        simulation.advance(stock, start)
        simulation.advance(stock, end)
        in_one_jump = [bar['close'] for bar in stock.price_history]

        stock.price_history = []
        simulation.advance(stock, start)
        for offset in range(1, (end - start).days + 1):
            simulation.advance(stock, start + timedelta(days=offset))
        day_by_day = [bar['close'] for bar in stock.price_history]

        self.assertEqual(in_one_jump, day_by_day)


class MarketBehaviourTests(TestCase):
    def test_prices_actually_move(self):
        """Regression: every holding showed +0.00% because nothing advanced."""
        stock = _stock(stock_type='growth')
        simulation.advance(stock, date(2026, 6, 30))

        closes = {bar['close'] for bar in stock.price_history}
        self.assertGreater(len(closes), 20)

    def test_stocks_share_a_market_factor(self):
        """Independent walks never produce the correlation that makes concentration risky."""
        day = date(2026, 6, 30)
        stocks = [
            _stock(symbol=f'S{index}', sector='Technology', stock_type='stable')
            for index in range(20)
        ]
        market = simulation.market_return(day)
        agreeing = sum(
            1 for stock in stocks if (simulation.daily_return(stock, day, 100.0) > 0) == (market > 0)
        )
        self.assertGreater(agreeing, 10)

    def test_a_session_cannot_move_more_than_the_limit(self):
        stock = _stock(stock_type='penny', volatility=0.4)
        for offset in range(120):
            move = simulation.daily_return(stock, date(2026, 1, 1) + timedelta(days=offset), 50.0)
            self.assertLessEqual(abs(move), simulation.MAX_DAILY_MOVE)

    def test_weekends_are_skipped(self):
        stock = _stock()
        simulation.advance(stock, date(2026, 6, 30))

        for bar in stock.price_history:
            with self.subTest(day=bar['date']):
                self.assertTrue(simulation.is_trading_day(date.fromisoformat(bar['date'])))

    def test_every_bar_is_a_valid_candle(self):
        stock = _stock(stock_type='volatile')
        simulation.advance(stock, date(2026, 6, 30))

        for bar in stock.price_history:
            with self.subTest(day=bar['date']):
                self.assertGreaterEqual(bar['high'], max(bar['open'], bar['close']))
                self.assertLessEqual(bar['low'], min(bar['open'], bar['close']))
                self.assertGreater(bar['low'], 0)

    def test_advancing_an_already_current_stock_does_nothing(self):
        stock = _stock()
        today = date(2026, 6, 30)
        simulation.advance(stock, today)
        before = list(stock.price_history)

        self.assertFalse(simulation.advance(stock, today))
        self.assertEqual(stock.price_history, before)

    def test_a_stable_stock_stays_near_its_base(self):
        """Mean reversion is what makes 'stable' mean something over years."""
        stock = _stock(stock_type='stable', base_price=100, current_price=100)
        simulation.advance(stock, date(2026, 12, 31))

        final = stock.price_history[-1]['close']
        self.assertGreater(final, 60)
        self.assertLess(final, 180)
