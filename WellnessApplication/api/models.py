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
    (0, 'High Anxiety, Low Activity'),
    (1, 'Moderate Anxiety, Moderate Activity'),
    (2, 'Low Anxiety, High Activity'),
    (3, 'Physical Risk'),
    (4, 'Wellness Seeker'),
    (5, 'Inactive'),

]


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('male', "Male"), ("female", "Female")], null=True, blank=True)
    height = models.FloatField(help_text="In centimeters", null=True, blank=True)
    weight = models.FloatField(help_text="In kgs", null=True, blank=True)
    self_reported_stress = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Stress level from 1-10",
        null=True, blank=True
    )
    gad7_score = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(21)],
        help_text="GAD-7 score from 0-21",
        null=True, blank=True
    )
    physical_activity_week = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        help_text="Physical activity level from 0-7 (days a week)",
        
        null=True, blank=True
    )
    importance_stress_reduction = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Importance of stress reduction from 1-5",
        
        null=True, blank=True
    )
    primary_goal = models.PositiveSmallIntegerField(
        choices=GOAL_CHOICES,
        help_text="Primary goal for using the app",
        null=True, blank=True   
    )
    workout_goal_days = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        help_text="Number of days per week you want to work out",
        null=True, blank=True
    )

    segment_label = models.PositiveSmallIntegerField(
        choices=SEGMENT_CHOICES,
        null=True, blank=True,
        help_text="Segment label based on user profile and activity",
    )
