from django.contrib import admin

from .models import (
    Achievement,
    ChallengeLeaderboard,
    CustomStock,
    DemoPortfolio,
    FinancialGoal,
    HistoricalCrisis,
    StockPredictionChallenge,
    StockPredictionQuestion,
    UserAchievement,
    UserProfile,
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'level', 'xp', 'streak')
    list_filter = ('level',)
    search_fields = ('user__username',)


@admin.register(DemoPortfolio)
class DemoPortfolioAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'updated_at')


@admin.register(CustomStock)
class CustomStockAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'name', 'current_price', 'change_percent', 'trend')
    list_filter = ('stock_type', 'trend')
    search_fields = ('symbol', 'name')


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'xp_reward', 'is_active')
    list_filter = ('category', 'is_active')


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ('user', 'achievement', 'unlocked_at')


@admin.register(ChallengeLeaderboard)
class ChallengeLeaderboardAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_score', 'current_streak', 'best_streak')


@admin.register(StockPredictionChallenge)
class StockPredictionChallengeAdmin(admin.ModelAdmin):
    list_display = ('user', 'stock_symbol', 'prediction_direction', 'is_correct', 'score')


@admin.register(StockPredictionQuestion)
class StockPredictionQuestionAdmin(admin.ModelAdmin):
    list_display = ('stock_symbol', 'stock_name', 'difficulty', 'is_active')


@admin.register(FinancialGoal)
class FinancialGoalAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'target_amount', 'current_amount')


@admin.register(HistoricalCrisis)
class HistoricalCrisisAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'difficulty', 'start_date', 'end_date')
