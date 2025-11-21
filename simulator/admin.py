from django.contrib import admin
from .models import Scenario, DecisionOption, UserScenarioLog, QuizRun

@admin.register(Scenario)
class ScenarioAdmin(admin.ModelAdmin):
    list_display = ['title', 'starting_balance']
    search_fields = ['title']

@admin.register(DecisionOption)
class DecisionOptionAdmin(admin.ModelAdmin):
    list_display = ['text', 'scenario', 'decision_type', 'score']
    list_filter = ['decision_type', 'scenario']
    search_fields = ['text']

@admin.register(UserScenarioLog)
class UserScenarioLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'scenario', 'final_balance', 'points_earned', 'date_played']
    list_filter = ['date_played']
    search_fields = ['user__username']

@admin.register(QuizRun)
class QuizRunAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_score', 'is_completed', 'created_at']
    list_filter = ['is_completed', 'created_at']
    search_fields = ['user__username']