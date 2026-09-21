"""
Tests for goal mode's instruments.

Deposits and SIPs move money between the practice account and holdings that are
valued rather than stored, so these pin the two things that would go wrong
quietly: the account total forgetting them, and the gate that keeps them out of
normal mode.
"""

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from users.models import DemoPortfolio, FinancialGoal, PracticeDeposit, PracticeSip
from users.portfolio import instruments
from users.portfolio.simulation import FUNDS, fund_nav
from users.portfolio.valuation import value_portfolio


class FundNavTests(TestCase):
    def test_a_nav_is_reproducible(self):
        day = date(2026, 5, 4)
        self.assertEqual(fund_nav('index', day), fund_nav('index', day))

    def test_funds_differ_from_each_other(self):
        day = date(2026, 5, 4)
        navs = {key: fund_nav(key, day) for key in FUNDS}
        self.assertEqual(len(set(navs.values())), len(navs))

    def test_gold_moves_against_the_market(self):
        """Ballast that falls with everything else is not ballast."""
        self.assertLess(FUNDS['gold']['beta'], 0)

    def test_an_unknown_instrument_returns_the_base(self):
        self.assertEqual(fund_nav('nonsense'), instruments.fund_nav.__globals__['FUND_BASE_NAV'])


class DepositTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('depositor', password='x')
        self.portfolio = DemoPortfolio.objects.create(user=self.user)

    def _deposit(self, **overrides):
        deposit = PracticeDeposit.objects.create(
            portfolio=self.portfolio,
            principal=Decimal('10000'),
            rate=Decimal('0.0700'),
            tenure_months=overrides.get('tenure_months', 12),
        )
        if 'opened_on' in overrides:
            PracticeDeposit.objects.filter(id=deposit.id).update(opened_on=overrides['opened_on'])
            deposit.refresh_from_db()
        return deposit

    def test_a_longer_tenure_earns_a_better_rate(self):
        self.assertGreater(instruments.fd_rate(60), instruments.fd_rate(12))

    def test_interest_accrues_with_time_held(self):
        deposit = self._deposit(opened_on=date.today() - timedelta(days=180))
        figures = instruments.deposit_value(deposit)
        self.assertGreater(figures['current_value'], 10_000)
        self.assertLess(figures['current_value'], figures['value_at_maturity'])

    def test_a_deposit_stops_accruing_after_maturity(self):
        deposit = self._deposit(tenure_months=12, opened_on=date.today() - timedelta(days=900))
        figures = instruments.deposit_value(deposit)
        self.assertTrue(figures['matured'])
        self.assertAlmostEqual(figures['current_value'], figures['value_at_maturity'], delta=1)

    def test_breaking_early_pays_less_than_holding(self):
        deposit = self._deposit(opened_on=date.today() - timedelta(days=200))
        full = instruments.deposit_value(deposit)['current_value']
        self.assertLess(instruments.break_value(deposit), full)

    def test_an_open_deposit_counts_towards_the_account(self):
        self._deposit()
        self.assertGreater(value_portfolio(self.portfolio)['other_value'], 0)


class SipTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('sipper', password='x')
        self.portfolio = DemoPortfolio.objects.create(user=self.user, balance=Decimal('50000'))
        self.sip = PracticeSip.objects.create(
            portfolio=self.portfolio, instrument='index', monthly_amount=Decimal('5000')
        )

    def test_running_a_sip_buys_units_and_spends_cash(self):
        executed = instruments.run_due_sips(self.portfolio)
        self.sip.refresh_from_db()

        self.assertEqual(len(executed), 1)
        self.assertGreater(self.sip.units, 0)
        self.assertEqual(float(self.sip.invested), 5000)
        self.assertEqual(float(self.portfolio.balance), 45_000)

    def test_a_sip_runs_once_a_month(self):
        instruments.run_due_sips(self.portfolio)
        self.assertEqual(instruments.run_due_sips(self.portfolio), [])

    def test_a_sip_does_not_run_without_the_cash(self):
        self.portfolio.balance = Decimal('100')
        self.portfolio.save(update_fields=['balance'])
        self.assertEqual(instruments.run_due_sips(self.portfolio), [])

    def test_a_stopped_sip_does_not_run(self):
        self.sip.active = False
        self.sip.save(update_fields=['active'])
        self.assertEqual(instruments.run_due_sips(self.portfolio), [])

    def test_units_are_valued_at_todays_nav(self):
        instruments.run_due_sips(self.portfolio)
        self.sip.refresh_from_db()

        figures = instruments.sip_value(self.sip)
        self.assertAlmostEqual(
            figures['current_value'], self.sip.units * fund_nav('index'), delta=0.01
        )

    def test_sip_holdings_count_towards_the_account(self):
        instruments.run_due_sips(self.portfolio)
        account = value_portfolio(self.portfolio)
        self.assertGreater(account['other_value'], 0)
        self.assertAlmostEqual(
            account['total_value'], account['balance'] + account['other_value'], delta=0.01
        )


class GoalModeGateTests(TestCase):
    """Deposits and SIPs are goal-mode instruments, and the gate has to hold."""

    def setUp(self):
        self.user = User.objects.create_user('gated', password='x')
        self.client.force_login(self.user)
        DemoPortfolio.objects.create(user=self.user)

    def _open_fd(self):
        return self.client.post(
            '/api/users/portfolio/deposits/open/',
            {'principal': 5000, 'tenure_months': 12},
            content_type='application/json',
        )

    def _start_sip(self):
        return self.client.post(
            '/api/users/portfolio/sips/start/',
            {'instrument': 'index', 'monthly_amount': 2000},
            content_type='application/json',
        )

    def _link_a_goal(self):
        goal = FinancialGoal.objects.create(
            user=self.user,
            title='Flat',
            target_amount=Decimal('1000000'),
            target_date=date.today() + timedelta(days=2000),
            linked=True,
        )
        return goal

    def test_deposits_are_refused_outside_goal_mode(self):
        self.assertEqual(self._open_fd().status_code, 400)

    def test_sips_are_refused_outside_goal_mode(self):
        self.assertEqual(self._start_sip().status_code, 400)

    def test_both_are_allowed_once_a_goal_is_linked(self):
        self._link_a_goal()
        self.assertEqual(self._open_fd().status_code, 201)
        self.assertEqual(self._start_sip().status_code, 201)

    def test_a_deposit_larger_than_the_balance_is_refused(self):
        self._link_a_goal()
        response = self.client.post(
            '/api/users/portfolio/deposits/open/',
            {'principal': 5_000_000, 'tenure_months': 12},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_a_sip_below_the_minimum_is_refused(self):
        self._link_a_goal()
        response = self.client.post(
            '/api/users/portfolio/sips/start/',
            {'instrument': 'index', 'monthly_amount': 10},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_an_unknown_fund_is_refused(self):
        self._link_a_goal()
        response = self.client.post(
            '/api/users/portfolio/sips/start/',
            {'instrument': 'crypto-moon', 'monthly_amount': 2000},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
