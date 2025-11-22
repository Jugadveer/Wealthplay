from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """Extended user profile with level, XP, and onboarding data"""
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    RISK_CHOICES = [
        ('safe', 'Play it safe'),
        ('balanced', 'Balanced approach'),
        ('aggressive', 'Higher returns, higher risk'),
    ]
    
    INVESTMENT_EXPERIENCE_CHOICES = [
        ('beginner', 'Complete beginner'),
        ('basics', 'Know the basics'),
        ('experienced', 'Fairly experienced'),
        ('very_experienced', 'Very experienced'),
    ]
    
    GOAL_CHOICES = [
        ('long_term_wealth', 'Build long-term wealth'),
        ('specific_goals', 'Save for specific goals'),
        ('learning', 'Just learning for now'),
        ('extra_income', 'Generate extra income'),
    ]
    
    TIMELINE_CHOICES = [
        ('less_than_1', 'Less than 1 year'),
        ('1_to_5', '1-5 years'),
        ('5_plus', '5+ years'),
    ]
    
    INITIAL_INVESTMENT_CHOICES = [
        ('under_10k', 'Under ₹10,000'),
        ('10k_50k', '₹10,000 - ₹50,000'),
        ('50k_1lakh', '₹50,000 - ₹1,00,000'),
        ('above_1lakh', 'Above ₹1,00,000'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    xp = models.IntegerField(default=0)
    confidence_score = models.FloatField(default=0.0)  # 0-100
    
    # Onboarding answers
    financial_goal = models.CharField(max_length=30, choices=GOAL_CHOICES, blank=True)
    investment_experience = models.CharField(max_length=30, choices=INVESTMENT_EXPERIENCE_CHOICES, blank=True)
    risk_comfort = models.CharField(max_length=20, choices=RISK_CHOICES, blank=True)
    initial_investment = models.CharField(max_length=20, choices=INITIAL_INVESTMENT_CHOICES, blank=True)
    investment_timeline = models.CharField(max_length=20, choices=TIMELINE_CHOICES, blank=True)
    onboarding_completed = models.BooleanField(default=False)
    
    # Demo portfolio
    demo_balance = models.DecimalField(max_digits=12, decimal_places=2, default=50000.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-xp']

    def __str__(self):
        return f"{self.user.username} - {self.level} - {self.xp} XP"

    def calculate_level_from_xp(self):
        """Calculate level based on XP"""
        if self.xp < 750:
            return 'beginner'
        elif self.xp < 1200:
            return 'intermediate'
        else:
            return 'advanced'
    
    def save(self, *args, **kwargs):
        # Auto-update level based on XP
        self.level = self.calculate_level_from_xp()
        super().save(*args, **kwargs)


class UserProgress(models.Model):
    STATUS_CHOICES = [
        ('locked', 'Locked'),
        ('unlocked', 'Unlocked'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress')
    
    # For JSON-based courses (primary fields)
    course_id = models.CharField(max_length=100, db_index=True, blank=True, default='')  # Course ID from JSON
    module_id = models.CharField(max_length=100, db_index=True, blank=True, default='')  # Module ID from JSON
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='locked')
    progress_percent = models.FloatField(default=0.0)
    xp_awarded = models.IntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_accessed = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Progress tracking fields
    flashcards_flipped = models.JSONField(default=list, blank=True)  # List of flashcard IDs that have been flipped
    mcqs_progress = models.JSONField(default=dict, blank=True)  # {mcq_id: {answered: bool, correct: bool, attempts: int}}

    class Meta:
        unique_together = [
            ['user', 'course_id', 'module_id'],
        ]
        indexes = [
            models.Index(fields=['user', 'course_id']),
            models.Index(fields=['user', 'course_id', 'module_id']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.course_id} - {self.module_id} - {self.status}"


class QuizAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    course_id = models.CharField(max_length=100, blank=True, default='')  # For JSON-based courses
    module_id = models.CharField(max_length=100, blank=True, default='')
    quiz_data = models.JSONField(default=dict)  # Store question_id, answer, etc.
    score = models.FloatField(default=0.0)
    max_score = models.FloatField(default=0.0)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-completed_at']

    def __str__(self):
        return f"{self.user.username} - {self.course_id} - {self.module_id} - {self.score}/{self.max_score}"


class DemoPortfolio(models.Model):
    """Demo portfolio for practice trading"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='demo_portfolio')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=50000.00)
    holdings = models.JSONField(default=dict)  # {stock_symbol: {quantity, avg_price, current_price}}
    total_value = models.DecimalField(max_digits=12, decimal_places=2, default=50000.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - Demo Portfolio"


class FinancialGoal(models.Model):
    """User's financial goals"""
    ICON_CHOICES = [
        ('smartphone', 'Smartphone'),
        ('plane', 'Plane'),
        ('home', 'Home'),
        ('car', 'Car'),
        ('graduation-cap', 'Graduation'),
        ('gem', 'Gem'),
        ('lightbulb', 'Lightbulb'),
        ('wallet', 'Wallet'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='financial_goals')
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=20, choices=ICON_CHOICES, default='wallet')
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    current_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    monthly_sip = models.DecimalField(max_digits=10, decimal_places=2)
    time_to_goal_months = models.IntegerField()
    color = models.CharField(max_length=50, default='from-brand-primary to-orange-500')
    icon_bg = models.CharField(max_length=50, default='bg-brand-50 text-brand-600')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.name}"
    
    @property
    def progress_percent(self):
        """Calculate progress percentage"""
        if self.target_amount > 0:
            return round(min(100, (self.current_amount / self.target_amount) * 100), 1)
        return 0.0
    
    @property
    def remaining_amount(self):
        """Calculate remaining amount to reach goal"""
        return max(0, self.target_amount - self.current_amount)
