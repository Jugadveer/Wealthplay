from django.contrib import admin
from .models import UserProfile, UserProgress, QuizAttempt, DemoPortfolio


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'level', 'xp', 'confidence_score', 'onboarding_completed', 'created_at']
    list_filter = ['level', 'onboarding_completed', 'investment_experience', 'risk_comfort']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'course_id', 'module_id', 'status', 'xp_awarded', 'progress_percent', 'completed_at']
    list_filter = ['status', 'course_id', 'created_at']
    search_fields = ['user__username', 'course_id', 'module_id']
    readonly_fields = ['created_at', 'last_accessed']
    ordering = ['-created_at']


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'course_id', 'module_id', 'score', 'max_score', 'completed_at']
    list_filter = ['course_id', 'completed_at']
    search_fields = ['user__username', 'course_id', 'module_id']
    readonly_fields = ['completed_at']
    ordering = ['-completed_at']


@admin.register(DemoPortfolio)
class DemoPortfolioAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_value', 'created_at', 'updated_at']
    search_fields = ['user__username']
    readonly_fields = ['created_at', 'updated_at']
