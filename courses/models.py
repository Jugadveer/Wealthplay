"""
Course progress.

Course *content* lives on disk and is read by :mod:`courses.content`; nothing is
stored in the database for it. This module holds only what is per-user, which
is progress.

The app previously carried eleven models here — ``Course``, ``Topic``,
``Lesson``, ``ModuleContent``, ``ModuleMCQ``, ``ModuleQNA``,
``ModuleMentorPrompt``, ``UserMCQAttempt``, ``UserPlaqueCardCompletion``,
``UserCourseCustomization`` and ``MentorPersona`` — describing a second copy of
the content pipeline. Every one of those tables held zero rows.
"""

from django.contrib.auth.models import User
from django.db import models


class UserCourseProgress(models.Model):
    """One learner's state in one module.

    A row with an empty ``module_id`` represents course-level progress, which is
    why ``module_id`` is blankable rather than required.
    """

    class Status(models.TextChoices):
        NOT_STARTED = 'not_started', 'Not started'
        IN_PROGRESS = 'in_progress', 'In progress'
        COMPLETED = 'completed', 'Completed'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_progress')
    course_id = models.CharField(max_length=100)
    module_id = models.CharField(max_length=100, blank=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NOT_STARTED)
    progress_percent = models.FloatField(default=0.0)

    # Ids of questions already answered correctly, so XP is awarded once.
    answered_questions = models.JSONField(default=list, blank=True)
    # Card ids the learner has flipped and rated, for the module progress bar.
    reviewed_cards = models.JSONField(default=list, blank=True)

    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_accessed = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'course_id', 'module_id']
        indexes = [
            models.Index(fields=['user', 'course_id']),
            models.Index(fields=['user', 'status']),
        ]
        verbose_name_plural = 'user course progress'

    def __str__(self):
        return f'{self.user.username} · {self.course_id}/{self.module_id} · {self.status}'
