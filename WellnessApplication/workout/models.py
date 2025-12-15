from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from api.models import CustomUser


class Activity(models.Model):
    ACTIVITY_TYPES = [
        ('exercise', 'Exercise'),
        ('meditation', 'Meditation'),
        ('journaling', 'Journaling'),
    ]
    
    # User & Context
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='activities')
    activity_name = models.CharField(max_length=200)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    
    # Metadata
    user_segment = models.CharField(max_length=100, null=True, blank=True)  # Which segment this activity is for
    rl_action_id = models.IntegerField(null=True, blank=True)  # Which RL action recommended this
    
    # Activity Details
    description = models.TextField()
    duration_minutes = models.IntegerField(validators=[MinValueValidator(1)])
    intensity = models.CharField(
        max_length=20,
        choices=[('Low', 'Low'), ('Moderate', 'Moderate'), ('High', 'High')]
    )
    instructions = models.JSONField(default=list)  # List of instruction steps
    
    # Timeline
    assigned_date = models.DateTimeField(null=True, blank=True)  # When activity was assigned to user
    completion_date = models.DateTimeField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    
    # User Feedback During Activity
    motivation_before = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        help_text="User motivation before starting activity (1-5)"
    )
    motivation_after = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        help_text="User motivation after completing activity (1-5)"
    )
    difficulty_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        help_text="How difficult was this activity? (1=too easy, 5=too hard)"
    )
    enjoyment_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        help_text="How much did you enjoy it? (1=hated it, 5=loved it)"
    )
    notes = models.TextField(blank=True, help_text="User's optional notes")
    
    # Calculated Metrics
    motivation_delta = models.IntegerField(
        null=True, blank=True,
        help_text="motivation_after - motivation_before"
    )
    is_motivating = models.BooleanField(
        default=False,
        help_text="True if motivation increased (motivation_after > motivation_before)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-assigned_date']
        verbose_name = 'Activity'
        verbose_name_plural = 'Activities'
    
    def __str__(self):
        return f"{self.activity_name} - {self.user.username}"
    
    def save(self, *args, **kwargs):
        """Calculate derived fields when saving"""
        if self.motivation_before and self.motivation_after:
            self.motivation_delta = self.motivation_after - self.motivation_before
            self.is_motivating = self.motivation_after > self.motivation_before
        super().save(*args, **kwargs)
    
    @property
    def engagement_contribution(self):
        """
        Calculate this activity's contribution to user engagement (0-1).
        Used by RL agent.
        """
        if not self.completed:
            return -0.1  # Penalty for incomplete
        
        contribution = 0
        
        # Completion bonus
        contribution += 0.5
        
        # Motivation increase bonus
        if self.is_motivating:
            contribution += 0.3
        
        # Enjoyment bonus
        if self.enjoyment_rating and self.enjoyment_rating >= 4:
            contribution += 0.2
        
        return min(1.0, contribution)  # Cap at 1.0


class WorkoutSession(models.Model):
    """
    Groups multiple activities into a single workout session.
    Tracks overall session metrics.
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='workout_sessions')
    activities = models.ManyToManyField(Activity, related_name='sessions')
    
    # Session Info
    session_type = models.CharField(
        max_length=50,
        choices=[('daily', 'Daily'), ('weekly', 'Weekly')],
        default='daily'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Session Metrics
    total_activities = models.IntegerField(default=0)
    completed_activities = models.IntegerField(default=0)
    completion_rate = models.FloatField(default=0.0)  # 0-1
    
    avg_motivation_before = models.FloatField(default=0.0)
    avg_motivation_after = models.FloatField(default=0.0)
    avg_motivation_delta = models.FloatField(default=0.0)
    
    total_duration_minutes = models.IntegerField(default=0)
    
    # Overall Rating
    overall_session_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        help_text="How was the overall session? (1-5)"
    )
    session_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - Session {self.created_at.date()}"
    
    def calculate_metrics(self):
        """Recalculate session metrics based on activities"""
        activities = self.activities.all()
        
        if activities.count() == 0:
            return
        
        self.total_activities = activities.count()
        self.completed_activities = activities.filter(completed=True).count()
        self.completion_rate = self.completed_activities / self.total_activities
        
        # Motivation calculations
        completed_activities = activities.filter(completed=True)
        if completed_activities.exists():
            self.avg_motivation_before = completed_activities.filter(
                motivation_before__isnull=False
            ).aggregate(
                avg=models.Avg('motivation_before')
            )['avg'] or 0.0
            
            self.avg_motivation_after = completed_activities.filter(
                motivation_after__isnull=False
            ).aggregate(
                avg=models.Avg('motivation_after')
            )['avg'] or 0.0
            
            self.avg_motivation_delta = completed_activities.filter(
                motivation_delta__isnull=False
            ).aggregate(
                avg=models.Avg('motivation_delta')
            )['avg'] or 0.0
        
        # Duration
        self.total_duration_minutes = activities.aggregate(
            total=models.Sum('duration_minutes')
        )['total'] or 0
        
        self.save(update_fields=[
            'total_activities', 'completed_activities', 'completion_rate',
            'avg_motivation_before', 'avg_motivation_after', 'avg_motivation_delta',
            'total_duration_minutes'
        ])
    
    @property
    def engagement_contribution(self):
        """
        Calculate this session's contribution to user engagement (0-1).
        Used by RL agent.
        """
        if self.completion_rate == 0:
            return -0.1
        
        contribution = 0
        
        # Completion rate bonus (0-0.5)
        contribution += self.completion_rate * 0.5
        
        # Motivation increase bonus (0-0.3)
        if self.avg_motivation_delta > 0:
            contribution += min(0.3, self.avg_motivation_delta / 5.0)
        
        # Overall rating bonus (0-0.2)
        if self.overall_session_rating and self.overall_session_rating >= 4:
            contribution += 0.2
        
        return min(1.0, contribution)  # Cap at 1.0
