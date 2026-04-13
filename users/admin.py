from django.contrib import admin
from .models import UserProfile, UserProgress, QuizAttempt, DemoPortfolio


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'level', 'xp', 'confidence_score', 'streak', 'created_at']
    list_filter = ['level', 'investment_experience', 'risk_tolerance']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'course_id', 'module_id', 'status', 'xp_awarded', 'progress_percent', 'last_accessed']
    list_filter = ['status', 'course_id']
    search_fields = ['user__username', 'course_id', 'module_id']
    readonly_fields = ['last_accessed']
    ordering = ['-last_accessed']


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'lesson', 'score', 'max_score', 'completed_at']
    list_filter = ['completed_at']
    search_fields = ['user__username']
    readonly_fields = ['completed_at']
    ordering = ['-completed_at']


@admin.register(DemoPortfolio)
class DemoPortfolioAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_value', 'created_at', 'updated_at']
    search_fields = ['user__username']
    readonly_fields = ['created_at', 'updated_at']
