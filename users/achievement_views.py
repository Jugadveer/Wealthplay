"""
API endpoints for achievements system
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from .models import Achievement, UserAchievement, UserProfile, ChallengeLeaderboard
from simulator.models import UserScenarioAttempt, QuizRun
from .models import DemoPortfolio, StockPredictionChallenge
from django.db.models import Count, Sum
import json
import traceback


ACHIEVEMENT_DEFAULTS = {
    'first_trade': {'name': 'First Trade', 'description': 'Execute your first stock trade', 'icon_name': 'briefcase', 'category': 'trading', 'xp_reward': 25},
    'portfolio_pro': {'name': 'Portfolio Pro', 'description': 'Build a diversified portfolio with 5+ stocks', 'icon_name': 'briefcase', 'category': 'trading', 'xp_reward': 100},
    'diversified': {'name': 'Diversified Investor', 'description': 'Own stocks across 3+ different sectors', 'icon_name': 'target', 'category': 'trading', 'xp_reward': 75},
    'risk_taker': {'name': 'Risk Taker', 'description': 'Make a trade worth over ₹10,000', 'icon_name': 'zap', 'category': 'trading', 'xp_reward': 50},
    'conservative': {'name': 'Conservative Investor', 'description': 'Maintain positive returns for 7+ days', 'icon_name': 'shield', 'category': 'trading', 'xp_reward': 75},
    'streak_5': {'name': '5-Day Streak', 'description': 'Log in and participate for 5 consecutive days', 'icon_name': 'flame', 'category': 'consistency', 'xp_reward': 50},
    'streak_10': {'name': '10-Day Streak', 'description': 'Maintain a 10-day activity streak', 'icon_name': 'flame', 'category': 'consistency', 'xp_reward': 100},
    'streak_30': {'name': '30-Day Streak', 'description': 'An incredible 30-day streak of learning', 'icon_name': 'flame', 'category': 'consistency', 'xp_reward': 300},
    'xp_100': {'name': 'Rising Star', 'description': 'Earn your first 100 XP', 'icon_name': 'sparkles', 'category': 'milestone', 'xp_reward': 25},
    'xp_500': {'name': 'XP Hunter', 'description': 'Accumulate 500 XP', 'icon_name': 'sparkles', 'category': 'milestone', 'xp_reward': 50},
    'xp_1000': {'name': 'XP Legend', 'description': 'Reach 1000 XP and beyond', 'icon_name': 'trophy', 'category': 'milestone', 'xp_reward': 150},
    'xp_2500': {'name': 'XP Legend+', 'description': 'Reach 2500 XP and beyond', 'icon_name': 'trophy', 'category': 'milestone', 'xp_reward': 250},
    'xp_milestone': {'name': 'XP Legend', 'description': 'Reach 1000 XP and beyond', 'icon_name': 'trophy', 'category': 'milestone', 'xp_reward': 150},
    'scenario_master': {'name': 'Scenario Master', 'description': 'Complete 5 financial scenario quizzes', 'icon_name': 'target', 'category': 'milestone', 'xp_reward': 100},
    'scenario_perfect': {'name': 'Perfect Scenario', 'description': 'Score perfectly on a scenario quiz', 'icon_name': 'check-circle-2', 'category': 'learning', 'xp_reward': 100},
    'stock_predictor': {'name': 'Stock Oracle', 'description': 'Make 10 stock predictions', 'icon_name': 'trending-up', 'category': 'milestone', 'xp_reward': 75},
    'stock_master': {'name': 'Stock Master', 'description': 'Make 50 correct stock predictions', 'icon_name': 'trending-up', 'category': 'milestone', 'xp_reward': 200},
    'perfect_quiz': {'name': 'Perfect Quiz', 'description': 'Score 80%+ on a scenario quiz', 'icon_name': 'check-circle-2', 'category': 'learning', 'xp_reward': 100},
    'profit_maker': {'name': 'Profit Maker', 'description': 'Achieve 10% portfolio returns', 'icon_name': 'trending-up', 'category': 'milestone', 'xp_reward': 200},
    'portfolio_master': {'name': 'Portfolio Master', 'description': 'Achieve 25% portfolio returns', 'icon_name': 'trending-up', 'category': 'milestone', 'xp_reward': 300},
}


def _ensure_achievement(achievement_id):
    defaults = ACHIEVEMENT_DEFAULTS.get(achievement_id)
    if not defaults:
        return None

    achievement, _ = Achievement.objects.get_or_create(
        id=achievement_id,
        defaults={**defaults, 'is_active': True},
    )

    dirty = False
    for field, value in defaults.items():
        if getattr(achievement, field) != value:
            setattr(achievement, field, value)
            dirty = True
    if not achievement.is_active:
        achievement.is_active = True
        dirty = True
    if dirty:
        achievement.save()

    return achievement


def check_and_unlock_achievements(user):
    """Check user's activity and unlock achievements"""
    unlocked = []
    
    try:
        profile, _ = UserProfile.objects.get_or_create(user=user)
    except Exception:
        return unlocked
    
    # Check XP milestones
    xp_milestones = [
        ('xp_100', 100),
        ('xp_500', 500),
        ('xp_1000', 1000),
        ('xp_2500', 2500),
    ]
    
    for ach_id, threshold in xp_milestones:
        if profile.xp >= threshold:
            achievement = _ensure_achievement(ach_id) or Achievement.objects.filter(id=ach_id, is_active=True).first()
            if achievement:
                user_ach, created = UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=achievement
                )
                if created:
                    unlocked.append(achievement)
    
    # Check streak achievements
    if profile.streak >= 5:
        achievement = _ensure_achievement('streak_5') or Achievement.objects.filter(id='streak_5', is_active=True).first()
        if achievement:
            user_ach, created = UserAchievement.objects.get_or_create(
                user=user,
                achievement=achievement
            )
            if created:
                unlocked.append(achievement)
    
    if profile.streak >= 10:
        achievement = _ensure_achievement('streak_10') or Achievement.objects.filter(id='streak_10', is_active=True).first()
        if achievement:
            user_ach, created = UserAchievement.objects.get_or_create(
                user=user,
                achievement=achievement
            )
            if created:
                unlocked.append(achievement)
    
    if profile.streak >= 30:
        achievement = _ensure_achievement('streak_30') or Achievement.objects.filter(id='streak_30', is_active=True).first()
        if achievement:
            user_ach, created = UserAchievement.objects.get_or_create(
                user=user,
                achievement=achievement
            )
            if created:
                unlocked.append(achievement)
    
    # Check portfolio achievements
    try:
        portfolio = DemoPortfolio.objects.get(user=user)
        holdings = portfolio.holdings or {}
        trade_history = portfolio.trade_history if isinstance(portfolio.trade_history, list) else []
        
        # First trade should unlock after any completed trade, even if holdings are later sold.
        has_completed_trade = len(holdings) > 0 or len(trade_history) > 0
        if has_completed_trade:
            achievement = _ensure_achievement('first_trade') or Achievement.objects.filter(id='first_trade', is_active=True).first()
            if achievement:
                # Only create if it doesn't exist - don't auto-unlock if already exists
                user_ach, created = UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=achievement
                )
                if created:
                    unlocked.append(achievement)
        
        # Diversified portfolio
        if len(holdings) >= 5:
            achievement = _ensure_achievement('diversified') or Achievement.objects.filter(id='diversified', is_active=True).first()
            if achievement:
                user_ach, created = UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=achievement
                )
                if created:
                    unlocked.append(achievement)
        
        # Portfolio Pro - 10% returns
        # Calculate from portfolio P/L
        try:
            from .portfolio_views import calculate_portfolio_data
            portfolio_data = calculate_portfolio_data(portfolio)
            total_pnl_percent = portfolio_data.get('total_pnl_percent', 0)
        except Exception as e:
            print(f"Error calculating portfolio data for achievements for user {user.id}: {e}")
            print(traceback.format_exc())
            total_pnl_percent = 0
        
        if total_pnl_percent >= 10:
            achievement = _ensure_achievement('profit_maker') or Achievement.objects.filter(id='profit_maker', is_active=True).first()
            if achievement:
                user_ach, created = UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=achievement
                )
                if created:
                    unlocked.append(achievement)
        
        # Portfolio Master - 25% returns
        if total_pnl_percent >= 25:
            achievement = _ensure_achievement('portfolio_master') or Achievement.objects.filter(id='portfolio_master', is_active=True).first()
            if achievement:
                user_ach, created = UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=achievement
                )
                if created:
                    unlocked.append(achievement)
        
    except DemoPortfolio.DoesNotExist:
        pass
    
    # Check scenario achievements
    try:
        scenario_attempts = UserScenarioAttempt.objects.filter(user=user)
        scenario_score = sum((attempt.score_earned or 0) for attempt in scenario_attempts)
    except Exception as e:
        print(f"Error calculating scenario score for achievements for user {user.id}: {e}")
        print(traceback.format_exc())
        scenario_score = 0
    
    if scenario_score >= 1000:
        achievement = _ensure_achievement('scenario_master') or Achievement.objects.filter(id='scenario_master', is_active=True).first()
        if achievement:
            user_ach, created = UserAchievement.objects.get_or_create(
                user=user,
                achievement=achievement
            )
            if created:
                unlocked.append(achievement)
    
    # Check for perfect scenario quiz
    try:
        perfect_quizzes = QuizRun.objects.filter(
            user=user,
            is_completed=True
        )
        for quiz in perfect_quizzes:
            try:
                scenario_list = quiz.get_scenario_list()
            except (TypeError, ValueError) as e:
                print(f"Skipping malformed quiz run {quiz.id} for achievements: {e}")
                continue

            max_possible = len(scenario_list) * 20
            if quiz.total_score >= max_possible:
                achievement = _ensure_achievement('scenario_perfect') or Achievement.objects.filter(id='scenario_perfect', is_active=True).first()
                if achievement:
                    user_ach, created = UserAchievement.objects.get_or_create(
                        user=user,
                        achievement=achievement
                    )
                    if created:
                        unlocked.append(achievement)
                break  # Only award once
    except Exception as e:
        print(f"Error checking quiz achievements for user {user.id}: {e}")
        print(traceback.format_exc())
    
    # Check stock prediction achievements
    try:
        predictions = StockPredictionChallenge.objects.filter(user=user, is_correct=True)
        correct_count = predictions.count()
    except Exception as e:
        print(f"Error checking stock prediction achievements for user {user.id}: {e}")
        print(traceback.format_exc())
        correct_count = 0
    
    if correct_count >= 10:
        achievement = _ensure_achievement('stock_predictor') or Achievement.objects.filter(id='stock_predictor', is_active=True).first()
        if achievement:
            user_ach, created = UserAchievement.objects.get_or_create(
                user=user,
                achievement=achievement
            )
            if created:
                unlocked.append(achievement)
    
    if correct_count >= 50:
        achievement = _ensure_achievement('stock_master') or Achievement.objects.filter(id='stock_master', is_active=True).first()
        if achievement:
            user_ach, created = UserAchievement.objects.get_or_create(
                user=user,
                achievement=achievement
            )
            if created:
                unlocked.append(achievement)
    
    # Award XP for newly unlocked achievements
    try:
        for achievement in unlocked:
            if achievement.xp_reward > 0:
                profile.xp += achievement.xp_reward
                profile.save()
    except Exception as e:
        print(f"Error awarding achievement XP for user {user.id}: {e}")
        print(traceback.format_exc())
    
    return unlocked


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_achievements(request):
    """Get all achievements with user's unlock status - USER-SPECIFIC"""
    try:
        # IMPORTANT: Only check for new achievements - don't auto-unlock incorrectly
        # This function will only unlock achievements if user actually meets criteria
        # For new users with no activity, this will return empty list
        check_and_unlock_achievements(request.user)
        
        all_achievements = Achievement.objects.filter(is_active=True).order_by('category', 'xp_reward')
        # CRITICAL: Only get achievements that actually have UserAchievement records with valid unlocked_at timestamps
        # This ensures new users with no activity show 0 achievements
        # Filter by the SPECIFIC USER to ensure achievements are user-specific
        user_achievements = UserAchievement.objects.filter(
            user=request.user,  # CRITICAL: Filter by current user only - ensures user-specific data
            unlocked_at__isnull=False  # Only include achievements with valid timestamps
        ).select_related('achievement')
        unlocked_ids = set(user_ach.achievement_id for user_ach in user_achievements)
        
        # Double-check: ensure we only count achievements that actually exist and are unlocked
        # For new users, this will be an empty set
        # This ensures achievements are truly user-specific
        
        achievements_data = []
        for achievement in all_achievements:
            is_unlocked = achievement.id in unlocked_ids
            unlocked_at = None
            
            # Only set unlocked_at if achievement is actually unlocked AND has a valid timestamp
            if is_unlocked:
                user_ach = next((ua for ua in user_achievements if ua.achievement_id == achievement.id), None)
                if user_ach and user_ach.unlocked_at:
                    unlocked_at = user_ach.unlocked_at.isoformat()
                else:
                    # If UserAchievement exists but has no unlocked_at, it's invalid - mark as locked
                    is_unlocked = False
            
            achievements_data.append({
                'id': achievement.id,
                'name': achievement.name,
                'description': achievement.description,
                'icon_name': achievement.icon_name,
                'category': achievement.category,
                'xp_reward': achievement.xp_reward,
                'unlocked': is_unlocked,  # Only true if UserAchievement exists AND has unlocked_at
                'unlocked_at': unlocked_at,  # Only set if actually unlocked with valid timestamp
            })
        
        return Response({
            'achievements': achievements_data,
            'total_unlocked': len(unlocked_ids),
            'total_available': all_achievements.count(),
        })
    except Exception as e:
        print(f"Error in check_achievements: {e}")
        print(traceback.format_exc())
        return Response({'newly_unlocked': [], 'count': 0, 'error': str(e)}, status=200)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_achievements(request):
    """Manually check and unlock achievements, return newly unlocked ones"""
    try:
        unlocked = check_and_unlock_achievements(request.user)
        
        unlocked_data = []
        for achievement in unlocked:
            unlocked_data.append({
                'id': achievement.id,
                'name': achievement.name,
                'description': achievement.description,
                'icon_name': achievement.icon_name,
                'xp_reward': achievement.xp_reward,
            })
        
        return Response({
            'newly_unlocked': unlocked_data,
            'count': len(unlocked_data),
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_achievement_notified(request):
    """Mark an achievement as notified (user has seen the popup)"""
    try:
        achievement_id = request.data.get('achievement_id')
        if not achievement_id:
            return Response({'error': 'achievement_id required'}, status=400)
        
        user_ach = UserAchievement.objects.get(
            user=request.user,
            achievement_id=achievement_id
        )
        user_ach.notified = True
        user_ach.save()
        
        return Response({'success': True})
    except UserAchievement.DoesNotExist:
        return Response({'error': 'Achievement not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

