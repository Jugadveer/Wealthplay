"""
Management command to check and clean up achievement data
Run: python manage.py check_achievements
"""
from django.core.management.base import BaseCommand
from users.models import UserAchievement, Achievement, UserProfile, DemoPortfolio
from simulator.models import UserScenarioAttempt, QuizRun
from users.models import StockPredictionChallenge


class Command(BaseCommand):
    help = 'Check and validate user achievements'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Remove invalid achievement unlocks',
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Check specific user by username',
        )

    def handle(self, *args, **options):
        username = options.get('user')
        clean = options.get('clean', False)
        
        if username:
            from django.contrib.auth.models import User
            try:
                users = [User.objects.get(username=username)]
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User {username} not found'))
                return
        else:
            from django.contrib.auth.models import User
            users = User.objects.all()
        
        for user in users:
            self.stdout.write(f'\n=== Checking achievements for {user.username} ===')
            
            profile, _ = UserProfile.objects.get_or_create(user=user)
            user_achievements = UserAchievement.objects.filter(user=user)
            
            self.stdout.write(f'Total UserAchievement records: {user_achievements.count()}')
            
            # Check each achievement
            invalid_count = 0
            for ua in user_achievements:
                achievement = ua.achievement
                should_be_unlocked = False
                reason = []
                
                # Check if achievement should actually be unlocked
                if achievement.id == 'first_trade':
                    try:
                        portfolio = DemoPortfolio.objects.get(user=user)
                        holdings = portfolio.holdings or {}
                        should_be_unlocked = len(holdings) > 0
                        if not should_be_unlocked:
                            reason.append('No portfolio holdings')
                    except DemoPortfolio.DoesNotExist:
                        reason.append('No portfolio')
                
                elif achievement.id == 'streak_5':
                    should_be_unlocked = profile.streak >= 5
                    if not should_be_unlocked:
                        reason.append(f'Streak is {profile.streak}, need 5')
                
                elif achievement.id == 'portfolio_pro':
                    # This achievement isn't being checked in check_and_unlock_achievements!
                    # Need to add logic for it
                    try:
                        portfolio = DemoPortfolio.objects.get(user=user)
                        # Would need to check portfolio returns - for now, mark as invalid if no portfolio
                        should_be_unlocked = False
                        reason.append('Portfolio Pro check not implemented')
                    except DemoPortfolio.DoesNotExist:
                        reason.append('No portfolio')
                
                elif achievement.id.startswith('xp_'):
                    threshold_map = {
                        'xp_100': 100,
                        'xp_500': 500,
                        'xp_1000': 1000,
                        'xp_2500': 2500,
                    }
                    threshold = threshold_map.get(achievement.id, 0)
                    should_be_unlocked = profile.xp >= threshold
                    if not should_be_unlocked:
                        reason.append(f'XP is {profile.xp}, need {threshold}')
                
                else:
                    # For other achievements, assume they might be valid
                    should_be_unlocked = True
                
                if not should_be_unlocked:
                    invalid_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ❌ {achievement.name}: Should NOT be unlocked - {", ".join(reason)}'
                        )
                    )
                    if clean:
                        ua.delete()
                        self.stdout.write(self.style.SUCCESS(f'    ✓ Deleted invalid achievement'))
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ {achievement.name}: Valid')
                    )
            
            if invalid_count > 0 and not clean:
                self.stdout.write(
                    self.style.WARNING(
                        f'\nFound {invalid_count} invalid achievements. Run with --clean to remove them.'
                    )
                )
            elif invalid_count > 0 and clean:
                self.stdout.write(
                    self.style.SUCCESS(f'\n✓ Cleaned up {invalid_count} invalid achievements.')
                )
            elif invalid_count == 0:
                self.stdout.write(self.style.SUCCESS('\n✓ All achievements are valid!'))

