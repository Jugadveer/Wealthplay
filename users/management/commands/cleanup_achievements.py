"""
Management command to clean up invalid achievement unlocks
Run: python manage.py cleanup_achievements
"""
from django.core.management.base import BaseCommand
from users.models import UserAchievement, UserProfile, DemoPortfolio
from simulator.models import UserScenarioAttempt, QuizRun
from users.models import StockPredictionChallenge


class Command(BaseCommand):
    help = 'Clean up invalid achievement unlocks for all users'

    def handle(self, *args, **options):
        from django.contrib.auth.models import User
        from users.portfolio_views import calculate_portfolio_data
        
        total_removed = 0
        
        for user in User.objects.all():
            profile, _ = UserProfile.objects.get_or_create(user=user)
            user_achievements = UserAchievement.objects.filter(user=user)
            
            removed_count = 0
            for ua in user_achievements:
                achievement = ua.achievement
                should_be_unlocked = False
                
                # Check if achievement should actually be unlocked
                if achievement.id == 'first_trade':
                    try:
                        portfolio = DemoPortfolio.objects.get(user=user)
                        holdings = portfolio.holdings or {}
                        should_be_unlocked = len(holdings) > 0
                    except DemoPortfolio.DoesNotExist:
                        should_be_unlocked = False
                
                elif achievement.id == 'streak_5':
                    should_be_unlocked = profile.streak >= 5
                
                elif achievement.id == 'streak_10':
                    should_be_unlocked = profile.streak >= 10
                
                elif achievement.id == 'streak_30':
                    should_be_unlocked = profile.streak >= 30
                
                elif achievement.id == 'portfolio_pro':
                    try:
                        portfolio = DemoPortfolio.objects.get(user=user)
                        portfolio_data = calculate_portfolio_data(portfolio)
                        total_pnl_percent = portfolio_data.get('total_pnl_percent', 0)
                        should_be_unlocked = total_pnl_percent >= 10
                    except DemoPortfolio.DoesNotExist:
                        should_be_unlocked = False
                
                elif achievement.id.startswith('xp_'):
                    threshold_map = {
                        'xp_100': 100,
                        'xp_500': 500,
                        'xp_1000': 1000,
                        'xp_2500': 2500,
                    }
                    threshold = threshold_map.get(achievement.id, 0)
                    should_be_unlocked = profile.xp >= threshold
                
                elif achievement.id == 'diversified':
                    try:
                        portfolio = DemoPortfolio.objects.get(user=user)
                        holdings = portfolio.holdings or {}
                        should_be_unlocked = len(holdings) >= 5
                    except DemoPortfolio.DoesNotExist:
                        should_be_unlocked = False
                
                elif achievement.id == 'scenario_master':
                    scenario_attempts = UserScenarioAttempt.objects.filter(user=user)
                    scenario_score = sum(attempt.score_earned for attempt in scenario_attempts)
                    should_be_unlocked = scenario_score >= 1000
                
                elif achievement.id == 'stock_predictor':
                    predictions = StockPredictionChallenge.objects.filter(user=user, is_correct=True)
                    should_be_unlocked = predictions.count() >= 10
                
                elif achievement.id == 'stock_master':
                    predictions = StockPredictionChallenge.objects.filter(user=user, is_correct=True)
                    should_be_unlocked = predictions.count() >= 50
                
                else:
                    # For other achievements, keep them (might be valid)
                    should_be_unlocked = True
                
                if not should_be_unlocked:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  Removing invalid achievement: {user.username} - {achievement.name}'
                        )
                    )
                    ua.delete()
                    removed_count += 1
                    total_removed += 1
            
            if removed_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Removed {removed_count} invalid achievements for {user.username}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Cleanup complete! Removed {total_removed} invalid achievements total.')
        )

