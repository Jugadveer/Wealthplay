from django.db import models
from django.contrib.auth.models import User


class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Topic(models.Model):
    course = models.ForeignKey(Course, related_name='topics', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Lesson(models.Model):
    topic = models.ForeignKey(Topic, related_name='lessons', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.topic.title} - {self.title}"


class MentorPersona(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    avatar_url = models.URLField(blank=True)

    def __str__(self):
        return self.name


# User-specific course customization (for future use)
class UserCourseCustomization(models.Model):
    """Store user-specific customizations for courses (different questions, content, etc.)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_customizations')
    course_id = models.CharField(max_length=100)  # Course ID from JSON
    custom_content = models.JSONField(default=dict, blank=True)  # Store custom Q&A, modules, etc.
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'course_id']
        indexes = [
            models.Index(fields=['user', 'course_id']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.course_id}"


# User-specific course progress tracking for JSON-based courses
class UserCourseProgress(models.Model):
    """Track user progress for JSON-based courses"""
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='json_course_progress')
    course_id = models.CharField(max_length=100)  # Course ID from JSON
    module_id = models.CharField(max_length=100, blank=True)  # Module ID from JSON
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    progress_percent = models.FloatField(default=0.0)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_accessed = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'course_id', 'module_id']
        indexes = [
            models.Index(fields=['user', 'course_id']),
            models.Index(fields=['user', 'course_id', 'module_id']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.course_id} - {self.status}"


# Enriched Module Content Models
class ModuleContent(models.Model):
    """Stores enriched content for JSON-based modules"""
    module_id = models.CharField(max_length=200, primary_key=True, db_index=True)  # Format: course_id_module_id
    course_id = models.CharField(max_length=100, db_index=True)  # Parent course ID
    title = models.CharField(max_length=300)
    summary = models.TextField(blank=True)
    theory_text = models.TextField(blank=True)
    duration_min = models.IntegerField(default=0)
    xp_reward = models.IntegerField(default=0)
    plaque_card = models.JSONField(default=dict, blank=True)  # Store plaque card config
    metadata = models.JSONField(default=dict, blank=True)  # Store metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['course_id']),
            models.Index(fields=['course_id', 'module_id']),
        ]

    def __str__(self):
        return f"{self.module_id} - {self.title}"


class ModuleQNA(models.Model):
    """Fixed Q&A pairs for modules"""
    module_content = models.ForeignKey(ModuleContent, related_name='qna_pairs', on_delete=models.CASCADE)
    question = models.TextField()
    answer = models.TextField()
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']
        indexes = [
            models.Index(fields=['module_content', 'order']),
        ]

    def __str__(self):
        return f"Q: {self.question[:50]}..."


class ModuleMCQ(models.Model):
    """Multiple Choice Questions for modules"""
    module_content = models.ForeignKey(ModuleContent, related_name='mcqs', on_delete=models.CASCADE)
    mcq_id = models.CharField(max_length=100)  # e.g., "mcq-1"
    question = models.TextField()
    choices = models.JSONField(default=list)  # ["A) ...", "B) ...", ...]
    correct_choice = models.CharField(max_length=1)  # "A", "B", "C", "D"
    explanation = models.TextField(blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']
        unique_together = ['module_content', 'mcq_id']
        indexes = [
            models.Index(fields=['module_content', 'order']),
        ]

    def __str__(self):
        return f"{self.mcq_id}: {self.question[:50]}..."


class ModuleMentorPrompt(models.Model):
    """Mentor prompt suggestions for modules"""
    module_content = models.ForeignKey(ModuleContent, related_name='mentor_prompts', on_delete=models.CASCADE)
    user_question = models.TextField()  # Sample question user might ask
    mentor_answer_seed = models.TextField()  # Seed answer for AI mentor
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']
        indexes = [
            models.Index(fields=['module_content', 'order']),
        ]

    def __str__(self):
        return f"Q: {self.user_question[:50]}..."


class UserMCQAttempt(models.Model):
    """Track user attempts at MCQs"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mcq_attempts')
    mcq = models.ForeignKey(ModuleMCQ, on_delete=models.CASCADE, related_name='attempts')
    selected_choice = models.CharField(max_length=1)
    is_correct = models.BooleanField(default=False)
    xp_awarded = models.IntegerField(default=0)
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'mcq']
        indexes = [
            models.Index(fields=['user', 'attempted_at']),
            models.Index(fields=['mcq', 'is_correct']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.mcq.mcq_id} - {'Correct' if self.is_correct else 'Incorrect'}"


class UserPlaqueCardCompletion(models.Model):
    """Track user completion of plaque cards"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='plaque_completions')
    module_content = models.ForeignKey(ModuleContent, on_delete=models.CASCADE, related_name='completions')
    card_type = models.CharField(max_length=50)  # quiz-card, flash-card, scenario-card, challenge-card
    xp_awarded = models.IntegerField(default=0)
    badge_earned = models.CharField(max_length=100, blank=True, null=True)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'module_content', 'card_type']
        indexes = [
            models.Index(fields=['user', 'completed_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.module_content.module_id} - {self.card_type}"
