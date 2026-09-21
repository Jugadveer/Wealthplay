"""
The daily edition: what brings someone back tomorrow.

Three ideas hold this together.

**One puzzle per day, shared by everyone.** ``DailyPuzzle`` is keyed on
``(date, kind)``, so every player gets the same Ticker Tiles round and results
are comparable. That is what makes a shared score worth posting.

**Streaks that survive one bad day.** A missed day normally resets the streak,
but a freeze — earned every seven days — absorbs one. Punishing a single missed
day is how habit apps lose the people they were working for.

**Review scheduled per user.** ``ReviewCard`` implements SM-2 spaced repetition
over questions from modules the learner has completed. Because intervals are
per-card and per-user, the drill does not repeat the same question two days
running, and the pool grows as they learn more.
"""

from __future__ import annotations

from datetime import date, timedelta

from django.contrib.auth.models import User
from django.db import models


class PuzzleKind(models.TextChoices):
    TICKER = 'ticker', 'Ticker Tiles'
    CALL = 'call', 'Market Call'
    ESTIMATE = 'estimate', 'Number Sense'


class DailyPuzzle(models.Model):
    """One day's puzzle of a given kind.

    ``payload`` holds what the client may see; ``solution`` holds what it must
    not. They are separate columns so a serialiser cannot leak the answer by
    forgetting to exclude a key.
    """

    puzzle_date = models.DateField(db_index=True)
    kind = models.CharField(max_length=16, choices=PuzzleKind.choices)
    payload = models.JSONField(default=dict)
    solution = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['puzzle_date', 'kind']
        ordering = ['-puzzle_date']
        indexes = [models.Index(fields=['puzzle_date', 'kind'])]

    def __str__(self):
        return f'{self.puzzle_date} {self.kind}'


class PuzzleAttempt(models.Model):
    """One player's run at one puzzle."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='puzzle_attempts')
    puzzle = models.ForeignKey(DailyPuzzle, on_delete=models.CASCADE, related_name='attempts')
    guesses = models.JSONField(default=list)
    solved = models.BooleanField(default=False)
    finished = models.BooleanField(default=False)
    score = models.IntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['user', 'puzzle']
        indexes = [models.Index(fields=['user', 'puzzle'])]

    def __str__(self):
        state = 'solved' if self.solved else 'finished' if self.finished else 'open'
        return f'{self.user.username} · {self.puzzle} · {state}'


class Streak(models.Model):
    """Daily participation, with freezes."""

    FREEZE_EVERY_DAYS = 7
    MAX_FREEZES = 3

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='daily_streak')
    current = models.IntegerField(default=0)
    longest = models.IntegerField(default=0)
    last_active = models.DateField(null=True, blank=True)
    freezes = models.IntegerField(default=1)
    total_days = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.user.username} · {self.current} day streak'

    def register(self, day: date | None = None) -> dict:
        """Record activity for ``day``. Idempotent within a day.

        Returns what changed, so the UI can say "streak saved by a freeze"
        rather than silently continuing the count.
        """
        day = day or date.today()

        if self.last_active == day:
            return {'changed': False, 'current': self.current, 'used_freeze': False}

        gap = (day - self.last_active).days if self.last_active else 1
        used_freeze = False

        if gap == 1 or self.last_active is None:
            self.current += 1
        elif gap == 2 and self.freezes > 0:
            # Exactly one missed day, and a freeze to spend on it.
            self.freezes -= 1
            self.current += 1
            used_freeze = True
        else:
            self.current = 1

        self.total_days += 1
        self.longest = max(self.longest, self.current)
        self.last_active = day

        earned_freeze = False
        if self.current % self.FREEZE_EVERY_DAYS == 0 and self.freezes < self.MAX_FREEZES:
            self.freezes += 1
            earned_freeze = True

        self.save()
        return {
            'changed': True,
            'current': self.current,
            'longest': self.longest,
            'used_freeze': used_freeze,
            'earned_freeze': earned_freeze,
            'freezes': self.freezes,
        }

    def status(self, today: date | None = None) -> dict:
        """Current state without recording activity."""
        today = today or date.today()
        gap = (today - self.last_active).days if self.last_active else None

        return {
            'current': self.current if gap is None or gap <= 1 else 0,
            'longest': self.longest,
            'freezes': self.freezes,
            'total_days': self.total_days,
            'active_today': self.last_active == today,
            'at_risk': gap == 1,
        }


class ReviewCard(models.Model):
    """One question in a learner's spaced-repetition queue.

    Implements SM-2: each successful recall multiplies the interval by an ease
    factor that itself drifts with performance, so easy material recedes and
    difficult material keeps coming back.
    """

    MIN_EASE = 1.3
    DEFAULT_EASE = 2.5

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='review_cards')
    course_id = models.CharField(max_length=100)
    module_id = models.CharField(max_length=100)
    question_id = models.CharField(max_length=100)

    question = models.TextField()
    options = models.JSONField(default=list)
    correct_index = models.IntegerField()
    explanation = models.TextField(blank=True)

    ease = models.FloatField(default=DEFAULT_EASE)
    interval_days = models.IntegerField(default=0)
    repetitions = models.IntegerField(default=0)
    due_on = models.DateField(default=date.today, db_index=True)

    lapses = models.IntegerField(default=0)
    reviews = models.IntegerField(default=0)

    class Meta:
        unique_together = ['user', 'question_id']
        ordering = ['due_on']
        indexes = [models.Index(fields=['user', 'due_on'])]

    def __str__(self):
        return f'{self.user.username} · {self.question_id} · due {self.due_on}'

    def review(self, correct: bool, today: date | None = None) -> None:
        """Apply one review outcome and reschedule.

        A wrong answer resets the interval but only nudges the ease factor down,
        so one slip does not make a card permanently hard.
        """
        today = today or date.today()
        self.reviews += 1

        if not correct:
            self.lapses += 1
            self.repetitions = 0
            self.interval_days = 1
            self.ease = max(self.MIN_EASE, self.ease - 0.2)
        else:
            self.repetitions += 1
            if self.repetitions == 1:
                self.interval_days = 1
            elif self.repetitions == 2:
                self.interval_days = 4
            else:
                self.interval_days = round(self.interval_days * self.ease)
            self.ease = min(3.0, self.ease + 0.05)

        self.due_on = today + timedelta(days=self.interval_days)
        self.save()
