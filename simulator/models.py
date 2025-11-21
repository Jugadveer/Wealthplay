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
    text = models.CharField(max_length=100)
    
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
    created_at = models.DateTimeField(auto_now_add=True)

    def get_scenario_list(self):
        if not self.scenario_ids or self.scenario_ids.strip() == '':
            return []
        return [int(id) for id in self.scenario_ids.split(',') if id.strip()]