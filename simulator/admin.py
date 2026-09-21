from django.contrib import admin

from .models import DecisionOption, QuizRun, Scenario, UserScenarioAttempt


class DecisionOptionInline(admin.TabularInline):
    model = DecisionOption
    extra = 0


@admin.register(Scenario)
class ScenarioAdmin(admin.ModelAdmin):
    list_display = ('title', 'starting_balance')
    inlines = [DecisionOptionInline]


@admin.register(QuizRun)
class QuizRunAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_score', 'current_question_index', 'is_completed', 'created_at')
    list_filter = ('is_completed',)


@admin.register(UserScenarioAttempt)
class UserScenarioAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'scenario', 'score_earned', 'is_correct', 'attempted_at')
