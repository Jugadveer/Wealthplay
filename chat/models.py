"""Mentor conversation history."""

from django.contrib.auth.models import User
from django.db import models


class TopicChatMessage(models.Model):
    """One turn of a mentor conversation, scoped to a module.

    ``module_id`` is blank for the floating assistant, which is not attached to
    any lesson.
    """

    class Sender(models.TextChoices):
        USER = 'user', 'Learner'
        NEX = 'nex', 'Nex'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mentor_messages')
    course_id = models.CharField(max_length=100, blank=True)
    module_id = models.CharField(max_length=100, blank=True)
    sender = models.CharField(max_length=10, choices=Sender.choices)
    text = models.TextField()
    time_display = models.CharField(max_length=10, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        indexes = [models.Index(fields=['user', 'course_id', 'module_id'])]

    def __str__(self):
        return f'{self.user.username} · {self.sender} · {self.text[:40]}'
