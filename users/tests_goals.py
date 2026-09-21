"""
Tests for the goal planner.

This module does arithmetic people will act on, so the tests check the numbers
against closed-form answers rather than against whatever the code produced when
it was written. They also pin the rule that makes this more than a calculator:
what a goal is *for* constrains how much risk its plan may carry.
"""

from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase

from users.goals import planner


class ArithmeticTests(TestCase):
    def test_future_value_compounds_monthly(self):
        # 1,00,000 at 12% for one year, compounded monthly, is 1,12,682.50.
        self.assertAlmostEqual(planner.future_value(100_000, 0.12, 12), 112_682.50, delta=1.0)

    def test_a_sip_reaches_what_it_should(self):
        # 10,000 a month at 12% for ten years is about 23.2 lakh.
        value = planner.sip_future_value(10_000, 0.12, 120)
        self.assertGreater(value, 2_300_000)
        self.assertLess(value, 2_350_000)

    def test_sip_required_inverts_sip_future_value(self):
        """The amount the planner asks for must actually reach the target."""
        needed = planner.sip_required(5_000_000, 0.11, 180)
        reached = planner.sip_future_value(needed, 0.11, 180)
        self.assertAlmostEqual(reached, 5_000_000, delta=1.0)

    def test_sip_required_accounts_for_what_is_already_saved(self):
        with_savings = planner.sip_required(5_000_000, 0.11, 180, present=1_000_000)
        without = planner.sip_required(5_000_000, 0.11, 180)
        self.assertLess(with_savings, without)

    def test_nothing_is_required_when_savings_already_get_there(self):
        self.assertEqual(planner.sip_required(100_000, 0.10, 120, present=5_000_000), 0.0)

    def test_emi_matches_the_standard_formula(self):
        # 30 lakh at 8.5% over 20 years is an EMI of about 26,035.
        loan = planner.emi(3_000_000, 0.085, 20)
        self.assertAlmostEqual(loan['monthly'], 26_035, delta=5)
        self.assertGreater(loan['total_interest'], loan['principal'])

    def test_months_until_never_returns_zero(self):
        today = date(2026, 9, 21)
        self.assertEqual(planner.months_until(date(2026, 9, 25), today), 1)
        self.assertEqual(planner.months_until(date(2027, 9, 21), today), 12)


class RiskRuleTests(TestCase):
    """The rule that makes this a planner rather than a compound-interest form."""

    def test_short_horizons_carry_no_equity(self):
        for criticality in ('critical', 'important', 'flexible'):
            with self.subTest(criticality=criticality):
                self.assertEqual(planner.equity_share(24, criticality), 0.0)

    def test_equity_rises_with_the_horizon(self):
        shares = [planner.equity_share(months, 'flexible') for months in (24, 48, 72, 108, 240)]
        self.assertEqual(shares, sorted(shares))
        self.assertGreater(shares[-1], shares[0])

    def test_a_critical_goal_carries_less_equity_than_a_flexible_one(self):
        """Regression against the thing most calculators get wrong.

        School fees and a holiday at the same horizon are not the same problem,
        and a planner that gives them the same allocation is not planning.
        """
        self.assertLess(planner.equity_share(180, 'critical'), planner.equity_share(180, 'flexible'))

    def test_growth_is_never_offered_for_a_goal_that_cannot_slip(self):
        plan = planner.build(
            target_amount=2_000_000,
            target_date=date(2046, 1, 1),
            category_key='education',
            today=date(2026, 1, 1),
        )
        self.assertNotIn('growth', [option['key'] for option in plan['plans']])

    def test_growth_is_offered_for_a_long_flexible_goal(self):
        plan = planner.build(
            target_amount=500_000,
            target_date=date(2036, 1, 1),
            category_key='travel',
            today=date(2026, 1, 1),
        )
        self.assertIn('growth', [option['key'] for option in plan['plans']])


class PlanTests(TestCase):
    def setUp(self):
        self.today = date(2026, 1, 1)

    def test_the_target_is_inflated_to_the_date(self):
        plan = planner.build(
            target_amount=1_000_000,
            target_date=date(2036, 1, 1),
            category_key='education',
            today=self.today,
        )
        # Ten years at 10% education inflation is about 2.59 times.
        self.assertGreater(plan['target_at_date'], 2_500_000)
        self.assertEqual(plan['inflation_percent'], 10.0)

    def test_education_inflates_faster_than_a_general_goal(self):
        args = dict(target_amount=1_000_000, target_date=date(2036, 1, 1), today=self.today)
        self.assertGreater(
            planner.build(category_key='education', **args)['target_at_date'],
            planner.build(category_key='general', **args)['target_at_date'],
        )

    def test_a_safer_plan_always_needs_more_each_month(self):
        plan = planner.build(
            target_amount=2_000_000,
            target_date=date(2041, 1, 1),
            category_key='travel',
            today=self.today,
        )
        by_key = {option['key']: option for option in plan['plans']}
        self.assertGreater(by_key['safe']['monthly_required'], by_key['balanced']['monthly_required'])
        self.assertGreater(by_key['balanced']['monthly_required'], by_key['growth']['monthly_required'])

    def test_every_plan_projects_the_target(self):
        """If a plan's monthly amount is followed, it must reach the number."""
        plan = planner.build(
            target_amount=3_000_000,
            target_date=date(2041, 1, 1),
            category_key='home',
            today=self.today,
        )
        for option in plan['plans']:
            with self.subTest(plan=option['key']):
                self.assertAlmostEqual(option['projected'], plan['target_at_date'], delta=2)

    def test_an_equity_plan_reports_a_downside_below_its_projection(self):
        plan = planner.build(
            target_amount=2_000_000,
            target_date=date(2041, 1, 1),
            category_key='travel',
            today=self.today,
        )
        growth = next(option for option in plan['plans'] if option['key'] == 'growth')
        self.assertLess(growth['downside'], growth['projected'])

    def test_feasibility_names_the_gap_when_the_plan_is_unaffordable(self):
        plan = planner.build(
            target_amount=10_000_000,
            target_date=date(2031, 1, 1),
            category_key='home',
            monthly_capacity=5_000,
            today=self.today,
        )
        feasibility = plan['feasibility']
        self.assertFalse(feasibility['achievable'])
        self.assertGreater(feasibility['shortfall_monthly'], 0)

    def test_feasibility_is_unknown_without_a_stated_capacity(self):
        plan = planner.build(
            target_amount=500_000,
            target_date=date(2031, 1, 1),
            category_key='travel',
            today=self.today,
        )
        self.assertFalse(plan['feasibility']['known'])

    def test_borrowing_is_only_offered_where_people_actually_borrow(self):
        home = planner.build(
            target_amount=2_000_000, target_date=date(2036, 1, 1),
            category_key='home', today=self.today,
        )
        travel = planner.build(
            target_amount=200_000, target_date=date(2031, 1, 1),
            category_key='travel', today=self.today,
        )
        self.assertIsNotNone(home['borrowing'])
        self.assertIsNone(travel['borrowing'])


class GoalLinkTests(TestCase):
    """Goal-based trading: one account, so at most one goal may claim it."""

    def setUp(self):
        self.user = User.objects.create_user('goaluser', password='x')
        self.client.force_login(self.user)

    def _create(self, title, category='general'):
        response = self.client.post(
            '/api/users/goals/create/',
            {
                'title': title,
                'category': category,
                'target_amount': 1_000_000,
                'target_date': '2036-01-01',
            },
            content_type='application/json',
        )
        return response.json()['goal']

    def _link(self, goal_id):
        return self.client.post(
            f'/api/users/goals/{goal_id}/link/',
            {'linked': True},
            content_type='application/json',
        )

    def test_linking_a_second_goal_unlinks_the_first(self):
        first, second = self._create('Flat'), self._create('Car', 'car')
        self._link(first['id'])
        self._link(second['id'])

        goals = {g['id']: g['linked'] for g in self.client.get('/api/users/goals/').json()['goals']}
        self.assertFalse(goals[first['id']])
        self.assertTrue(goals[second['id']])

    def test_a_linked_goal_reports_the_account_as_its_progress(self):
        goal = self._create('Flat')
        self._link(goal['id'])

        data = self.client.get('/api/users/goals/').json()
        linked = next(g for g in data['goals'] if g['linked'])
        self.assertEqual(linked['current_amount'], data['account']['total_value'])

    def test_a_contribution_is_paid_once_a_month(self):
        self.client.post(
            '/api/users/goals/contribution/',
            {'monthly_contribution': 5_000},
            content_type='application/json',
        )

        first = self.client.post('/api/users/goals/contribution/pay/', {},
                                 content_type='application/json')
        second = self.client.post('/api/users/goals/contribution/pay/', {},
                                  content_type='application/json')

        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json()['credited'], 5_000)
        self.assertEqual(second.status_code, 400)

    def test_paying_in_without_setting_an_amount_is_refused(self):
        response = self.client.post('/api/users/goals/contribution/pay/', {},
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_a_goal_in_the_past_is_refused(self):
        response = self.client.post(
            '/api/users/goals/create/',
            {'title': 'Yesterday', 'target_amount': 1000, 'target_date': '2020-01-01'},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
