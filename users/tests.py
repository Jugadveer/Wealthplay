"""
Tests for the money paths.

These cover the arithmetic that is easy to get wrong and expensive to get wrong:
currency conversion on a foreign holding, the achievement rules, and the streak's
freeze logic. Each one pins a bug that actually shipped.

Run with:  python manage.py test
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from daily.models import Streak
from market_data.services import Quote
from users.achievement_views import CATALOGUE, check_and_unlock_achievements
from users.models import DemoPortfolio, UserAchievement, UserProfile
from users.portfolio.valuation import value_portfolio


def fake_quote(symbol, price, currency='USD', sector='Technology'):
    return Quote(
        symbol=symbol,
        name=symbol,
        price=price,
        change_percent=0.0,
        currency=currency,
        sector=sector,
    )


class ForeignHoldingValuationTests(TestCase):
    """A dollar holding must be converted exactly once.

    Regression: `buy_stock` stored the cost basis already converted to INR while
    `valuation` converted it again, so a flat AAPL position showed as −98%.
    """

    def setUp(self):
        self.user = User.objects.create_user('trader', password='x')
        UserProfile.objects.create(user=self.user)

    def _portfolio(self, holdings):
        return DemoPortfolio.objects.create(
            user=self.user, balance=Decimal('10000'), holdings=holdings
        )

    @patch('users.portfolio.pricing.usd_to_inr', return_value=Decimal('85'))
    @patch('market_data.services.get_quote')
    def test_unchanged_dollar_price_is_flat(self, get_quote, _rate):
        get_quote.return_value = fake_quote('AAPL', 300.0)
        portfolio = self._portfolio({'AAPL': {'quantity': 2, 'avg_price': 300.0}})

        result = value_portfolio(portfolio)
        holding = result['holdings'][0]

        # 2 × $300 × ₹85 = ₹51,000, invested and current alike.
        self.assertAlmostEqual(holding['invested'], 51_000, places=2)
        self.assertAlmostEqual(holding['current_value'], 51_000, places=2)
        self.assertAlmostEqual(result['total_pnl_percent'], 0.0, places=6)

    @patch('users.portfolio.pricing.usd_to_inr', return_value=Decimal('85'))
    @patch('market_data.services.get_quote')
    def test_gain_is_reported_in_percent_not_currency_drift(self, get_quote, _rate):
        get_quote.return_value = fake_quote('AAPL', 330.0)
        portfolio = self._portfolio({'AAPL': {'quantity': 1, 'avg_price': 300.0}})

        result = value_portfolio(portfolio)
        self.assertAlmostEqual(result['total_pnl_percent'], 10.0, places=4)

    @patch('market_data.services.get_quote')
    def test_rupee_holding_is_not_converted(self, get_quote):
        get_quote.return_value = fake_quote('RELIANCE', 1200.0, currency='INR')
        portfolio = self._portfolio({'RELIANCE': {'quantity': 10, 'avg_price': 1000.0}})

        holding = value_portfolio(portfolio)['holdings'][0]
        self.assertAlmostEqual(holding['invested'], 10_000, places=2)
        self.assertAlmostEqual(holding['current_value'], 12_000, places=2)

    @patch('market_data.services.get_quote')
    def test_provider_outage_falls_back_to_cost_not_zero(self, get_quote):
        """A dead provider must not render a position as a total loss."""
        get_quote.return_value = fake_quote('AAPL', 0.0, currency='INR')
        portfolio = self._portfolio({'AAPL': {'quantity': 1, 'avg_price': 500.0}})

        result = value_portfolio(portfolio)
        self.assertAlmostEqual(result['total_pnl_percent'], 0.0, places=6)


class AchievementTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('learner', password='x')
        UserProfile.objects.create(user=self.user, xp=0)

    @patch('market_data.services.get_quote')
    def test_first_trade_unlocks_and_grants_xp_once(self, get_quote):
        """Regression: XP was granted inline and again in a trailing pass."""
        get_quote.return_value = fake_quote('AECB', 100.0, currency='INR')
        DemoPortfolio.objects.create(
            user=self.user,
            balance=Decimal('40000'),
            holdings={'AECB': {'quantity': 10, 'avg_price': 100.0}},
        )

        first = check_and_unlock_achievements(self.user)
        self.assertIn('first_trade', [a.id for a in first])

        reward = next(rule.xp for rule in CATALOGUE if rule.id == 'first_trade')
        self.assertEqual(UserProfile.objects.get(user=self.user).xp, reward)

        # Re-running must be a no-op, not a second payout.
        self.assertEqual(check_and_unlock_achievements(self.user), [])
        self.assertEqual(UserProfile.objects.get(user=self.user).xp, reward)

    def test_no_achievements_without_activity(self):
        self.assertEqual(check_and_unlock_achievements(self.user), [])
        self.assertEqual(UserAchievement.objects.filter(user=self.user).count(), 0)

    def test_catalogue_ids_are_unique(self):
        ids = [rule.id for rule in CATALOGUE]
        self.assertEqual(len(ids), len(set(ids)))


class StreakTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('daily', password='x')
        self.streak = Streak.objects.create(user=self.user)

    def test_consecutive_days_accumulate(self):
        start = date(2026, 1, 1)
        for offset in range(3):
            self.streak.register(start + timedelta(days=offset))
        self.assertEqual(self.streak.current, 3)

    def test_second_visit_same_day_changes_nothing(self):
        today = date(2026, 1, 1)
        self.streak.register(today)
        result = self.streak.register(today)

        self.assertFalse(result['changed'])
        self.assertEqual(self.streak.current, 1)

    def test_one_missed_day_spends_a_freeze(self):
        self.streak.register(date(2026, 1, 1))
        result = self.streak.register(date(2026, 1, 3))

        self.assertTrue(result['used_freeze'])
        self.assertEqual(self.streak.current, 2)
        self.assertEqual(self.streak.freezes, 0)

    def test_two_missed_days_resets(self):
        self.streak.register(date(2026, 1, 1))
        self.streak.register(date(2026, 1, 5))

        self.assertEqual(self.streak.current, 1)
        # The freeze is kept: it could not have saved a two-day gap.
        self.assertEqual(self.streak.freezes, 1)

    def test_a_week_earns_a_freeze(self):
        self.streak.freezes = 0
        start = date(2026, 1, 1)
        for offset in range(7):
            self.streak.register(start + timedelta(days=offset))

        self.assertEqual(self.streak.current, 7)
        self.assertEqual(self.streak.freezes, 1)

    def test_longest_is_kept_after_a_reset(self):
        start = date(2026, 1, 1)
        for offset in range(4):
            self.streak.register(start + timedelta(days=offset))
        self.streak.register(start + timedelta(days=30))

        self.assertEqual(self.streak.current, 1)
        self.assertEqual(self.streak.longest, 4)
