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


def check_and_unlock_achievements(user):
    """Check user's activity and unlock achievements"""
    unlocked = []
    
    try:
        profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
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
            achievement = Achievement.objects.filter(id=ach_id, is_active=True).first()
            if achievement:
                user_ach, created = UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=achievement
                )
                if created:
                    unlocked.append(achievement)
    
    # Check streak achievements
    if profile.streak >= 5:
        achievement = Achievement.objects.filter(id='streak_5', is_active=True).first()
        if achievement:
            user_ach, created = UserAchievement.objects.get_or_create(
                user=user,
                achievement=achievement
            )
            if created:
                unlocked.append(achievement)
    
    if profile.streak >= 10:
        achievement = Achievement.objects.filter(id='streak_10', is_active=True).first()
        if achievement:
            user_ach, created = UserAchievement.objects.get_or_create(
                user=user,
                achievement=achievement
            )
            if created:
                unlocked.append(achievement)
    
    if profile.streak >= 30:
        achievement = Achievement.objects.filter(id='streak_30', is_active=True).first()
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
        
        # First trade - only unlock if user has actually made a trade
        # Check if there are any holdings OR if there's a trade history
        # For now, just check holdings count - a new user with empty portfolio won't get this
        if len(holdings) > 0:
            achievement = Achievement.objects.filter(id='first_trade', is_active=True).first()
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
            achievement = Achievement.objects.filter(id='diversified', is_active=True).first()
            if achievement:
                user_ach, created = UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=achievement
                )
                if created:
                    unlocked.append(achievement)
        
        # Portfolio Pro - 10% returns
        # Calculate from portfolio P/L
        from .portfolio_views import calculate_portfolio_data
        portfolio_data = calculate_portfolio_data(portfolio)
        total_pnl_percent = portfolio_data.get('total_pnl_percent', 0)
        
        if total_pnl_percent >= 10:
            achievement = Achievement.objects.filter(id='portfolio_pro', is_active=True).first()
            if achievement:
                user_ach, created = UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=achievement
                )
                if created:
                    unlocked.append(achievement)
        
        # Portfolio Master - 25% returns
        if total_pnl_percent >= 25:
            achievement = Achievement.objects.filter(id='portfolio_master', is_active=True).first()
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
    scenario_attempts = UserScenarioAttempt.objects.filter(user=user)
    scenario_score = sum(attempt.score_earned for attempt in scenario_attempts)
    
    if scenario_score >= 1000:
        achievement = Achievement.objects.filter(id='scenario_master', is_active=True).first()
        if achievement:
            user_ach, created = UserAchievement.objects.get_or_create(
                user=user,
                achievement=achievement
            )
            if created:
                unlocked.append(achievement)
    
    # Check for perfect scenario quiz
    perfect_quizzes = QuizRun.objects.filter(
        user=user,
        is_completed=True
    )
    for quiz in perfect_quizzes:
        scenario_list = quiz.get_scenario_list()
        max_possible = len(scenario_list) * 20
        if quiz.total_score >= max_possible:
            achievement = Achievement.objects.filter(id='scenario_perfect', is_active=True).first()
            if achievement:
                user_ach, created = UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=achievement
                )
                if created:
                    unlocked.append(achievement)
            break  # Only award once
    
    # Check stock prediction achievements
    predictions = StockPredictionChallenge.objects.filter(user=user, is_correct=True)
    correct_count = predictions.count()
    
    if correct_count >= 10:
        achievement = Achievement.objects.filter(id='stock_predictor', is_active=True).first()
        if achievement:
            user_ach, created = UserAchievement.objects.get_or_create(
                user=user,
                achievement=achievement
            )
            if created:
                unlocked.append(achievement)
    
    if correct_count >= 50:
        achievement = Achievement.objects.filter(id='stock_master', is_active=True).first()
        if achievement:
            user_ach, created = UserAchievement.objects.get_or_create(
                user=user,
                achievement=achievement
            )
            if created:
                unlocked.append(achievement)
    
    # Award XP for newly unlocked achievements
    for achievement in unlocked:
        if achievement.xp_reward > 0:
            profile.xp += achievement.xp_reward
            profile.save()
    
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
        return Response({'error': str(e)}, status=500)


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

