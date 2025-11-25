"""
Management command to create default achievements
Run: python manage.py create_achievements
"""
from django.core.management.base import BaseCommand
from users.models import Achievement


class Command(BaseCommand):
    help = 'Creates default achievements'

    def handle(self, *args, **options):
        achievements_data = [
            {
                'id': 'first_trade',
                'name': 'First Trade',
                'description': 'Completed your first demo trade',
                'icon_name': 'sparkles',
                'category': 'trading',
                'xp_reward': 50,
            },
            {
                'id': 'streak_5',
                'name': '5 Day Streak',
                'description': 'Maintained a 5-day learning streak',
                'icon_name': 'flame',
                'category': 'consistency',
                'xp_reward': 100,
            },
            {
                'id': 'streak_10',
                'name': '10 Day Streak',
                'description': 'Maintained a 10-day learning streak',
                'icon_name': 'flame',
                'category': 'consistency',
                'xp_reward': 250,
            },
            {
                'id': 'streak_30',
                'name': '30 Day Streak',
                'description': 'Maintained a 30-day learning streak',
                'icon_name': 'flame',
                'category': 'consistency',
                'xp_reward': 1000,
            },
            {
                'id': 'portfolio_pro',
                'name': 'Portfolio Pro',
                'description': 'Achieved 10% returns on demo portfolio',
                'icon_name': 'trending-up',
                'category': 'trading',
                'xp_reward': 200,
            },
            {
                'id': 'portfolio_master',
                'name': 'Portfolio Master',
                'description': 'Achieved 25% returns on demo portfolio',
                'icon_name': 'trending-up',
                'category': 'trading',
                'xp_reward': 500,
            },
            {
                'id': 'scenario_master',
                'name': 'Scenario Master',
                'description': 'Scored 1000+ points in scenario quizzes',
                'icon_name': 'target',
                'category': 'learning',
                'xp_reward': 300,
            },
            {
                'id': 'scenario_perfect',
                'name': 'Perfect Scenario',
                'description': 'Got a perfect score on a scenario quiz',
                'icon_name': 'trophy',
                'category': 'learning',
                'xp_reward': 150,
            },
            {
                'id': 'stock_predictor',
                'name': 'Stock Predictor',
                'description': 'Made 10 correct stock predictions',
                'icon_name': 'bar-chart-3',
                'category': 'trading',
                'xp_reward': 200,
            },
            {
                'id': 'stock_master',
                'name': 'Stock Master',
                'description': 'Made 50 correct stock predictions',
                'icon_name': 'bar-chart-3',
                'category': 'trading',
                'xp_reward': 750,
            },
            {
                'id': 'xp_100',
                'name': 'Getting Started',
                'description': 'Earned 100 XP',
                'icon_name': 'award',
                'category': 'milestone',
                'xp_reward': 0,
            },
            {
                'id': 'xp_500',
                'name': 'Rising Star',
                'description': 'Earned 500 XP',
                'icon_name': 'award',
                'category': 'milestone',
                'xp_reward': 0,
            },
            {
                'id': 'xp_1000',
                'name': 'Expert Trader',
                'description': 'Earned 1000 XP',
                'icon_name': 'award',
                'category': 'milestone',
                'xp_reward': 0,
            },
            {
                'id': 'xp_2500',
                'name': 'Master Trader',
                'description': 'Earned 2500 XP',
                'icon_name': 'award',
                'category': 'milestone',
                'xp_reward': 0,
            },
            {
                'id': 'diversified',
                'name': 'Diversified Portfolio',
                'description': 'Hold 5+ different stocks in your portfolio',
                'icon_name': 'briefcase',
                'category': 'trading',
                'xp_reward': 150,
            },
            {
                'id': 'risk_taker',
                'name': 'Risk Taker',
                'description': 'Made 10 high-risk trades',
                'icon_name': 'zap',
                'category': 'trading',
                'xp_reward': 100,
            },
            {
                'id': 'conservative',
                'name': 'Conservative Investor',
                'description': 'Maintained a low-risk portfolio for 7 days',
                'icon_name': 'shield',
                'category': 'trading',
                'xp_reward': 150,
            },
            {
                'id': 'course_complete',
                'name': 'Course Complete',
                'description': 'Completed your first course',
                'icon_name': 'book-open',
                'category': 'learning',
                'xp_reward': 200,
            },
            {
                'id': 'quiz_master',
                'name': 'Quiz Master',
                'description': 'Scored 100% on 5 quizzes',
                'icon_name': 'check-circle-2',
                'category': 'learning',
                'xp_reward': 250,
            },
            {
                'id': 'early_bird',
                'name': 'Early Bird',
                'description': 'Logged in 7 days in a row',
                'icon_name': 'sun',
                'category': 'consistency',
                'xp_reward': 100,
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for ach_data in achievements_data:
            achievement, created = Achievement.objects.update_or_create(
                id=ach_data['id'],
                defaults=ach_data
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  Created: {achievement.name}'))
            else:
                updated_count += 1
                self.stdout.write(f'  Updated: {achievement.name}')
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Achievements created/updated!\n'
            f'  Created: {created_count}\n'
            f'  Updated: {updated_count}\n'
            f'  Total: {Achievement.objects.count()}'
        ))

