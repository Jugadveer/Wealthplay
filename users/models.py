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
    financial_goal = models.CharField(max_length=50, choices=GOAL_CHOICES, blank=True)
    risk_tolerance = models.CharField(max_length=20, choices=RISK_CHOICES, blank=True)
    investment_experience = models.CharField(max_length=20, choices=INVESTMENT_EXPERIENCE_CHOICES, blank=True)
    timeline = models.CharField(max_length=20, choices=TIMELINE_CHOICES, blank=True)
    initial_investment = models.CharField(max_length=20, choices=INITIAL_INVESTMENT_CHOICES, blank=True)
    
    # Streak tracking
    streak = models.IntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def calculate_level_from_xp(self):
        """Calculate and update user level based on XP"""
        if self.xp >= 1200:
            new_level = 'advanced'
        elif self.xp >= 750:
            new_level = 'intermediate'
        else:
            new_level = 'beginner'
        
        # Update level if it changed
        if self.level != new_level:
            self.level = new_level
            self.save(update_fields=['level'])
        
        return new_level
    
    def save(self, *args, **kwargs):
        """Override save to auto-update level based on XP"""
        # Calculate level before saving
        if self.xp >= 1200:
            self.level = 'advanced'
        elif self.xp >= 750:
            self.level = 'intermediate'
        else:
            self.level = 'beginner'
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.username} - {self.level} - {self.xp} XP"
    
    class Meta:
        ordering = ['-xp']


class UserProgress(models.Model):
    """Track user progress through courses"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress')
    course_id = models.CharField(max_length=100)
    module_id = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, default='not_started')  # not_started, in_progress, completed
    progress_percent = models.FloatField(default=0.0)
    xp_awarded = models.IntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_accessed = models.DateTimeField(auto_now=True)
    flashcards_flipped = models.IntegerField(default=0)
    mcqs_progress = models.JSONField(default=dict, blank=True)
    
    class Meta:
        unique_together = ['user', 'course_id', 'module_id']
        ordering = ['-last_accessed']


class QuizAttempt(models.Model):
    """Track quiz attempts"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    lesson = models.ForeignKey('courses.Lesson', on_delete=models.CASCADE, null=True, blank=True)
    quiz_data = models.JSONField(default=dict)
    score = models.FloatField(default=0.0)
    max_score = models.FloatField(default=0.0)
    completed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-completed_at']


class DemoPortfolio(models.Model):
    """Demo portfolio for practice trading"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='demo_portfolio')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=50000.00)
    holdings = models.JSONField(default=dict)  # {symbol: {quantity, avg_price}}
    total_value = models.DecimalField(max_digits=12, decimal_places=2, default=50000.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Portfolio - ₹{self.balance}"


class ChallengeLeaderboard(models.Model):
    """Leaderboard for stock prediction challenges and scenario quizzes"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='challenge_leaderboard')
    total_score = models.IntegerField(default=0)  # Combined total of stock + scenario scores
    stock_score = models.IntegerField(default=0)  # Score from stock prediction challenges
    scenario_score = models.IntegerField(default=0)  # Score from scenario quizzes
    total_predictions = models.IntegerField(default=0)  # Stock predictions count
    correct_predictions = models.IntegerField(default=0)  # Correct stock predictions
    scenario_attempts = models.IntegerField(default=0)  # Scenario quiz attempts
    current_streak = models.IntegerField(default=0)
    best_streak = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-total_score', '-current_streak']
    
    def __str__(self):
        return f"{self.user.username} - Score: {self.total_score}, Streak: {self.current_streak}"


class StockPredictionChallenge(models.Model):
    """Track user's stock prediction challenges"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stock_predictions')
    stock_symbol = models.CharField(max_length=20)
    prediction = models.TextField()
    prediction_direction = models.CharField(max_length=10, default='neutral')  # up, down, neutral
    ai_analysis = models.TextField(blank=True)
    ai_direction = models.CharField(max_length=20, default='neutral')  # bullish, bearish, neutral
    is_correct = models.BooleanField(default=False)
    score = models.IntegerField(default=0)
    feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.stock_symbol} - {self.prediction_direction}"


class PredictedStockData(models.Model):
    """Cache for pre-calculated stock data, price history, and ML predictions"""
    symbol = models.CharField(max_length=20, unique=True, db_index=True)
    
    # Basic stock info (cached from yfinance)
    name = models.CharField(max_length=200, blank=True)
    current_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    change_percent = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    category = models.CharField(max_length=50, default='Unknown')
    sector = models.CharField(max_length=100, default='Unknown')
    market_cap = models.CharField(max_length=50, default='N/A')
    currency = models.CharField(max_length=3, default='USD')  # USD or INR
    
    # Price history (JSON field storing array of price data)
    price_history = models.JSONField(default=list, blank=True)
    
    # ML prediction results (cached)
    ml_direction = models.CharField(max_length=20, choices=[
        ('bullish', 'Bullish'),
        ('bearish', 'Bearish'),
        ('neutral', 'Neutral'),
    ], default='neutral')
    ml_confidence = models.FloatField(default=0.5)
    ml_regime = models.CharField(max_length=20, default='Unknown')
    ml_volatility = models.FloatField(default=0.0)
    
    # Metadata
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['symbol']
        indexes = [
            models.Index(fields=['symbol']),
            models.Index(fields=['last_updated']),
        ]
    
    def __str__(self):
        return f"{self.symbol} - {self.current_price} - {self.ml_direction}"


class CustomStock(models.Model):
    """Custom virtual stocks with simulated behavior patterns"""
    symbol = models.CharField(max_length=20, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    base_price = models.DecimalField(max_digits=12, decimal_places=2)
    current_price = models.DecimalField(max_digits=12, decimal_places=2)
    change_percent = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    
    # Stock characteristics
    STOCK_TYPE_CHOICES = [
        ('penny', 'Penny Stock'),
        ('volatile', 'Highly Volatile'),
        ('stable', 'Stable Blue Chip'),
        ('growth', 'Growth Stock'),
        ('dividend', 'Dividend Stock'),
        ('tech', 'Tech Stock'),
        ('finance', 'Finance Stock'),
        ('energy', 'Energy Stock'),
    ]
    stock_type = models.CharField(max_length=20, choices=STOCK_TYPE_CHOICES, default='stable')
    sector = models.CharField(max_length=100, default='General')
    category = models.CharField(max_length=50, default='Mid Cap')
    
    # Behavior parameters
    volatility = models.FloatField(default=0.02)  # Daily volatility (2% default)
    trend = models.CharField(max_length=10, default='neutral')  # bullish, bearish, neutral
    trend_strength = models.FloatField(default=0.0)  # 0.0 to 1.0
    
    # Price history (JSON field)
    price_history = models.JSONField(default=list, blank=True)
    
    # Metadata
    currency = models.CharField(max_length=3, default='INR')
    market_cap = models.CharField(max_length=50, default='N/A')
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['symbol']
        indexes = [
            models.Index(fields=['symbol']),
            models.Index(fields=['stock_type']),
        ]
    
    def __str__(self):
        return f"{self.symbol} - {self.name} - ₹{self.current_price}"


class FinancialGoal(models.Model):
    """User financial goals"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='financial_goals')
    title = models.CharField(max_length=200, default='Financial Goal')
    name = models.CharField(max_length=200, blank=True)  # Alias for title, for frontend compatibility
    description = models.TextField(blank=True)
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    current_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    monthly_sip = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    target_date = models.DateField(null=True, blank=True)
    time_to_goal_months = models.IntegerField(null=True, blank=True)  # Months to reach goal
    icon = models.CharField(max_length=50, default='wallet', blank=True)  # Icon name for frontend
    color = models.CharField(max_length=100, default='from-brand-primary to-orange-500', blank=True)  # Gradient color
    icon_bg = models.CharField(max_length=100, default='bg-brand-50 text-brand-600', blank=True)  # Icon background
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def progress_percent(self):
        """Calculate progress percentage"""
        if not self.target_amount or self.target_amount == 0:
            return 0
        return min(100, max(0, (float(self.current_amount) / float(self.target_amount)) * 100))
    
    @property
    def remaining_amount(self):
        """Calculate remaining amount to reach goal"""
        return max(0, float(self.target_amount) - float(self.current_amount))
    
    def save(self, *args, **kwargs):
        """Override save to sync name and title"""
        if self.name and not self.title:
            self.title = self.name
        elif self.title and not self.name:
            self.name = self.title
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.username} - {self.name or self.title}"


class Achievement(models.Model):
    """Achievement definitions"""
    ACHIEVEMENT_TYPES = [
        ('first_trade', 'First Trade'),
        ('streak_5', '5 Day Streak'),
        ('streak_10', '10 Day Streak'),
        ('streak_30', '30 Day Streak'),
        ('portfolio_pro', 'Portfolio Pro'),
        ('scenario_master', 'Scenario Master'),
        ('stock_predictor', 'Stock Predictor'),
        ('xp_milestone', 'XP Milestone'),
        ('perfect_quiz', 'Perfect Quiz'),
        ('diversified', 'Diversified Portfolio'),
        ('risk_taker', 'Risk Taker'),
        ('conservative', 'Conservative Investor'),
    ]
    
    id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon_name = models.CharField(max_length=50, default='trophy')  # Icon identifier for frontend
    category = models.CharField(max_length=50, default='general')
    xp_reward = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['category', 'xp_reward']
    
    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    """Track user's unlocked achievements"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)
    notified = models.BooleanField(default=False)  # Track if user has seen the notification
    
    class Meta:
        unique_together = ['user', 'achievement']
        ordering = ['-unlocked_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"


class StockPredictionQuestion(models.Model):
    """Fake stock prediction questions with charts and expected answers"""
    # Use real stock names but with fake data
    stock_name = models.CharField(max_length=200)  # e.g., "Apple Inc.", "Microsoft Corporation"
    stock_symbol = models.CharField(max_length=20, unique=True)  # e.g., "AAPL", "MSFT"
    
    # Question data
    question = models.TextField()  # The question text
    chart_data = models.JSONField(default=list)  # Price history for the chart
    
    # Expected answer (for AI analysis, not exact match)
    expected_direction = models.CharField(max_length=10, choices=[
        ('up', 'Upward Trend'),
        ('down', 'Downward Trend'),
        ('neutral', 'Neutral/Flat'),
    ], default='neutral')
    expected_keywords = models.JSONField(default=list)  # Keywords that should be in answer
    explanation = models.TextField()  # Explanation of the correct answer
    
    # Scoring
    base_score = models.IntegerField(default=10)
    max_score = models.IntegerField(default=20)
    
    # Metadata
    difficulty = models.CharField(max_length=20, choices=[
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ], default='medium')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.stock_symbol} - {self.question[:50]}..."
