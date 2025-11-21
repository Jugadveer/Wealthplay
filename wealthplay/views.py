from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from users.models import UserProfile, UserProgress

@login_required
def dashboard(request):
    """Dashboard for authenticated users"""
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user, level='beginner', xp=0)
    
    # Calculate streak (simplified - based on last activity)
    # For now, we'll calculate based on recent progress/completions
    recent_progress = UserProgress.objects.filter(
        user=request.user,
        completed_at__isnull=False
    ).order_by('-completed_at')
    
    streak = 0
    if recent_progress.exists():
        # Simple streak calculation (can be enhanced)
        today = timezone.now().date()
        last_completion = recent_progress.first().completed_at.date()
        if last_completion == today or last_completion == today - timedelta(days=1):
            streak = 3  # Placeholder - can be calculated more accurately
    
    # Calculate XP progress for next level
    level_xp_requirements = {
        'beginner': {'current': 0, 'next': 200, 'next_level': 'Intermediate'},
        'intermediate': {'current': 200, 'next': 500, 'next_level': 'Advanced'},
        'advanced': {'current': 500, 'next': 1000, 'next_level': 'Expert'}
    }
    
    level_info = level_xp_requirements.get(profile.level, level_xp_requirements['beginner'])
    current_xp = profile.xp
    xp_needed = max(0, current_xp - level_info['current'])
    xp_total = level_info['next'] - level_info['current']
    xp_percent = min(100, (xp_needed / xp_total * 100)) if xp_total > 0 else 0
    next_level_xp = level_info['next']
    
    # Get achievements (simplified)
    achievements = []
    completed_modules = UserProgress.objects.filter(user=request.user, status='completed').count()
    if completed_modules > 0:
        achievements.append({'icon': '👣', 'name': 'First Step', 'earned': True})
    if completed_modules > 5:
        achievements.append({'icon': '📊', 'name': 'First Trade', 'earned': True})
    if streak >= 5:
        achievements.append({'icon': '🔥', 'name': '5 Day Streak', 'earned': True})
    if completed_modules > 10:
        achievements.append({'icon': '💼', 'name': 'Portfolio Pro', 'earned': True})
    
    # Today's tip (can be rotated daily)
    tips = [
        "Investing is like planting a mango tree. You plant today, water it regularly, and enjoy the fruits years later. The key is to start early and stay consistent!",
        "The best time to start investing was yesterday. The second best time is today. Even small amounts compound into significant wealth over time.",
        "Don't put all your eggs in one basket. Diversification helps protect your investments from market volatility.",
        "Time in the market beats timing the market. Stay invested for the long term rather than trying to predict short-term movements.",
    ]
    import random
    today_tip = random.choice(tips)
    
    context = {
        'profile': profile,
        'user': request.user,
        'streak': streak,
        'current_xp': current_xp,
        'xp_needed': xp_needed,
        'xp_total': xp_total,
        'xp_percent': xp_percent,
        'next_level': level_info['next_level'],
        'next_level_xp': next_level_xp,
        'xp_until_next': max(0, next_level_xp - current_xp),
        'achievements': achievements,
        'today_tip': today_tip,
    }
    
    return render(request, 'dashboard.html', context)


def home(request):
    """Landing page for non-authenticated users"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'landing.html')
