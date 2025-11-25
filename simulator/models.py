from django.db import models
from django.contrib.auth.models import User

class Scenario(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    starting_balance = models.DecimalField(max_digits=10, decimal_places=2, default=50000)
    
    def __str__(self):
        return self.title

class DecisionOption(models.Model):
    scenario = models.ForeignKey(Scenario, related_name='options', on_delete=models.CASCADE)
    text = models.TextField()  # Changed to TextField to support longer option text
    
    TYPE_CHOICES = [
        ('INVEST', 'Invest'),
        ('SAVE', 'Save'),
        ('SPEND', 'Spend'),
    ]
    decision_type = models.CharField(max_length=10, choices=TYPE_CHOICES)

    # Logic
    balance_impact = models.DecimalField(max_digits=10, decimal_places=2)
    confidence_delta = models.IntegerField(default=0)
    risk_score_delta = models.IntegerField(default=0)
    future_growth_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0.0)
    
    # SCORING (New)
    score = models.IntegerField(default=0, help_text="Points awarded for this choice (0-20)")

    # Feedback
    why_it_matters = models.TextField()
    mentor_feedback = models.CharField(max_length=255)

    def __str__(self):
        return self.text

class UserScenarioLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, null=True, blank=True)
    chosen_option = models.CharField(max_length=200, null=True, blank=True) 
    final_balance = models.DecimalField(max_digits=12, decimal_places=2)
    points_earned = models.IntegerField(default=0)
    date_played = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_played']

# NEW MODEL FOR QUIZ SESSIONS
class QuizRun(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # Store scenario IDs as a comma-separated string "1,5,12,3,9"
    scenario_ids = models.CharField(max_length=100)
    current_question_index = models.IntegerField(default=0)
    total_score = models.IntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    xp_awarded = models.BooleanField(default=False)  # Track if XP was already awarded
    created_at = models.DateTimeField(auto_now_add=True)

    def get_scenario_list(self):
        if not self.scenario_ids or self.scenario_ids.strip() == '':
            return []
        return [int(id) for id in self.scenario_ids.split(',') if id.strip()]


class UserScenarioAttempt(models.Model):
    """Track user-specific scenario attempts with scores"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scenario_attempts')
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE)
    quiz_run = models.ForeignKey(QuizRun, on_delete=models.CASCADE, null=True, blank=True, related_name='attempts')
    chosen_option = models.ForeignKey(DecisionOption, on_delete=models.SET_NULL, null=True, blank=True)
    score_earned = models.IntegerField(default=0)  # Score for this specific attempt
    is_correct = models.BooleanField(default=False)  # Whether they chose the highest scoring option
    xp_awarded = models.IntegerField(default=0)  # XP awarded for this attempt
    attempted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-attempted_at']
        # Ensure one attempt per user per scenario per quiz run
        unique_together = ['user', 'scenario', 'quiz_run']
        indexes = [
            models.Index(fields=['user', 'scenario']),
            models.Index(fields=['user', 'attempted_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.scenario.title} - {self.score_earned}pts"