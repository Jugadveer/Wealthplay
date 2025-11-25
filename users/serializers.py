from rest_framework import serializers
from .models import UserProgress, QuizAttempt, UserProfile, DemoPortfolio


class UserProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProgress
        fields = ['id', 'user', 'course_id', 'module_id', 'status', 'progress_percent', 'xp_awarded', 'started_at', 'completed_at', 'last_accessed', 'flashcards_flipped', 'mcqs_progress']


class QuizAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAttempt
        fields = ['id', 'user', 'course_id', 'module_id', 'quiz_data', 'score', 'max_score', 'completed_at']


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'level', 'xp', 'confidence_score', 'financial_goal', 'investment_experience', 
                  'risk_tolerance', 'timeline', 'initial_investment', 'streak', 'last_activity_date', 'created_at', 'updated_at']


class DemoPortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemoPortfolio
        fields = ['id', 'user', 'holdings', 'total_value', 'created_at', 'updated_at']
