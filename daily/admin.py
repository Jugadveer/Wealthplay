from django.contrib import admin

from .models import DailyPuzzle, PuzzleAttempt, ReviewCard, Streak


@admin.register(DailyPuzzle)
class DailyPuzzleAdmin(admin.ModelAdmin):
    list_display = ('puzzle_date', 'kind', 'created_at')
    list_filter = ('kind', 'puzzle_date')


@admin.register(PuzzleAttempt)
class PuzzleAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'puzzle', 'solved', 'score', 'finished_at')
    list_filter = ('solved', 'finished')


@admin.register(Streak)
class StreakAdmin(admin.ModelAdmin):
    list_display = ('user', 'current', 'longest', 'freezes', 'last_active')


@admin.register(ReviewCard)
class ReviewCardAdmin(admin.ModelAdmin):
    list_display = ('user', 'question_id', 'due_on', 'repetitions', 'lapses')
    list_filter = ('due_on',)
