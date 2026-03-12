from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator





GOAL_CHOICES = [
    (0, 'Improve Fitness'),
    (1, 'Increase Mindfulness'),
    (2, 'Lose Weight'),
    (3, 'Reduce Stress'),
]


SEGMENT_CHOICES = [
    (0, 'Older High Stress Exhausted'),
    (1, 'Young High Stress Active Social'),
    (2, 'Mid Life Low Stress Depressed'),
    (3, 'Mid Life Thriving Wellness Seeker'),
    (4, 'Working Professional Sedentary Stable'),
]


class CustomUser(AbstractUser):
    # Basic User Fields
    email = models.EmailField(unique=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=[('male', "Male"), ("female", "Female"), ('other', 'Other')],
        null=True, blank=True
    )
    
    # Dietary Information
    diet_type = models.CharField(
        max_length=20,
        choices=[
            ('vegetarian', 'Vegetarian'),
            ('vegan', 'Vegan'),
            ('balanced', 'Balanced'),
            ('junk_food', 'Junk Food'),
            ('keto', 'Keto')
        ],
        null=True, blank=True,
        help_text="User's dietary preference"
    )
    
    # Mental Health and Wellness
    stress_level = models.CharField(
        max_length=10,
        choices=[
            ('low', 'Low'),
            ('moderate', 'Moderate'),
            ('high', 'High')
        ],
        null=True, blank=True,
        help_text="Self-reported stress level"
    )
    mental_health_condition = models.CharField(
        max_length=15,
        choices=[
            ('none', 'None'),
            ('ptsd', 'PTSD'),
            ('depression', 'Depression'),
            ('anxiety', 'Anxiety'),
            ('bipolar', 'Bipolar')
        ],
        null=True, blank=True,
        help_text="Mental health condition"
    )
    
    # Lifestyle Metrics
    exercise_level = models.CharField(
        max_length=10,
        choices=[
            ('low', 'Low'),
            ('moderate', 'Moderate'),
            ('high', 'High')
        ],
        null=True, blank=True,
        help_text="Exercise level"
    )
    sleep_hours = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(9)],
        help_text="Average sleep hours per night (0-9)",
        null=True, blank=True
    )
    work_hours_per_week = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Work hours per week (0-100)",
        null=True, blank=True
    )
    screen_time_per_day = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(24)],
        help_text="Screen time per day in hours (0-24)",
        null=True, blank=True
    )
    
    # Self-Reported Scores
    self_reported_social_interaction_score = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Social interaction score (0-10)",
        null=True, blank=True
    )
    happiness_score = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Self-reported happiness score (0-10)",
        null=True, blank=True
    )
    
    # Goals
    primary_goal = models.PositiveSmallIntegerField(
        choices=GOAL_CHOICES,
        help_text="Primary goal for using the app",
        null=True, blank=True   
    )
    workout_goal_days = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(7)],
        help_text="Number of days per week you want to work out",
        null=True, blank=True
    )

    segment_label = models.PositiveSmallIntegerField(
        choices=SEGMENT_CHOICES,
        null=True, blank=True,
        help_text="Segment label based on user profile and activity",
    )
    
    # RL Agent tracking fields
    engagement_score = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="User engagement score (0-1) for RL agent",
    )
    motivation_score = models.PositiveIntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="User motivation score (1-5) for RL agent",
    )
    workouts_completed = models.PositiveIntegerField(
        default=0,
        help_text="Total number of workouts completed",
    )
    meditation_sessions = models.PositiveIntegerField(
        default=0,
        help_text="Total number of meditation sessions completed",
    )
    last_action_recommended = models.PositiveIntegerField(
        default=5,
        help_text="Last RL action recommended (0-5)",
        null=True, blank=True,
    )
    last_recommendation_date = models.DateTimeField(
        auto_now=False,
        null=True, blank=True,
        help_text="When the last RL recommendation was made",
    )


class UserStatistics(models.Model):
    """
    Model to track aggregated user statistics for performance and analytics.
    Can be updated periodically or on activity completion.
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='statistics')
    
    # Activity Counts
    total_activities_completed = models.PositiveIntegerField(default=0)
    total_activities_assigned = models.PositiveIntegerField(default=0)
    
    # By Type
    total_exercises = models.PositiveIntegerField(default=0)
    total_meditations = models.PositiveIntegerField(default=0)
    total_journaling = models.PositiveIntegerField(default=0)
    
    # Engagement Metrics
    current_streak_days = models.PositiveIntegerField(default=0, help_text="Consecutive days with completed activities")
    longest_streak_days = models.PositiveIntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)
    
    # Performance Averages
    avg_motivation_improvement = models.FloatField(default=0.0, help_text="Average motivation delta across activities")
    avg_enjoyment_rating = models.FloatField(default=0.0)
    avg_difficulty_rating = models.FloatField(default=0.0)
    
    # Time Metrics
    total_minutes_exercised = models.PositiveIntegerField(default=0)
    total_minutes_meditated = models.PositiveIntegerField(default=0)
    
    # Weekly Metrics (rolling 7 days)
    activities_this_week = models.PositiveIntegerField(default=0)
    minutes_this_week = models.PositiveIntegerField(default=0)
    
    # Monthly Metrics (rolling 30 days)
    activities_this_month = models.PositiveIntegerField(default=0)
    minutes_this_month = models.PositiveIntegerField(default=0)
    
    # Completion Rate
    overall_completion_rate = models.FloatField(default=0.0, help_text="Percentage of assigned activities completed")
    
    # Timestamps
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'User Statistics'
        verbose_name_plural = 'User Statistics'
    
    def __str__(self):
        return f"Statistics for {self.user.username}"
