"""
Signals for automatic statistics updates.
Updates UserStatistics when activities are completed.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from workout.models import Activity, WorkoutSession
from .models import UserStatistics

User = get_user_model()


@receiver(post_save, sender=Activity)
def update_statistics_on_activity_save(sender, instance, created, **kwargs):
    """
    Update user statistics whenever an activity is completed.
    Triggered when Activity is saved (created or updated).
    """
    if instance.completed:
        user = instance.user
        _update_user_statistics(user)


@receiver(post_delete, sender=Activity)
def update_statistics_on_activity_delete(sender, instance, **kwargs):
    """
    Update user statistics when an activity is deleted.
    """
    user = instance.user
    _update_user_statistics(user)


@receiver(post_save, sender=WorkoutSession)
def update_statistics_on_workout_save(sender, instance, created, **kwargs):
    """
    Update user statistics when a workout session is saved.
    """
    user = instance.user
    _update_user_statistics(user)


@receiver(post_delete, sender=WorkoutSession)
def update_statistics_on_workout_delete(sender, instance, **kwargs):
    """
    Update user statistics when a workout session is deleted.
    """
    user = instance.user
    _update_user_statistics(user)


def _update_user_statistics(user):
    """
    Calculate and update all statistics for a user.
    This is called by signal handlers to keep statistics in sync.
    """
    from django.db.models import Count, Sum, Avg
    from django.utils import timezone
    from datetime import timedelta
    
    # Get or create statistics object
    stats, created = UserStatistics.objects.get_or_create(user=user)
    
    # Calculate completed activities
    completed_activities = Activity.objects.filter(
        user=user,
        completed=True
    )
    
    stats.total_activities_completed = completed_activities.count()
    
    # Calculate total duration from workout sessions
    workout_sessions = WorkoutSession.objects.filter(user=user)
    duration_sum = workout_sessions.aggregate(
        total=Sum('duration_minutes')
    )['total'] or 0
    stats.total_duration_minutes = duration_sum
    
    # Average session length
    if stats.total_activities_completed > 0:
        stats.average_session_length = duration_sum / stats.total_activities_completed
    else:
        stats.average_session_length = 0
    
    # Calculate calories burned
    calories_sum = completed_activities.aggregate(
        total=Sum('calories_burned')
    )['total'] or 0
    stats.total_calories_burned = calories_sum
    
    # Calculate average motivation
    motivation_avg = completed_activities.exclude(
        motivation_level__isnull=True
    ).aggregate(
        avg=Avg('motivation_level')
    )['avg'] or 0
    stats.average_motivation = round(motivation_avg, 2)
    
    # Calculate average performance rating
    rating_avg = completed_activities.exclude(
        performance_rating__isnull=True
    ).aggregate(
        avg=Avg('performance_rating')
    )['avg'] or 0
    stats.average_performance_rating = round(rating_avg, 2)
    
    # Calculate current streak
    stats.current_streak = _calculate_streak(user)
    
    # Calculate longest streak
    longest_streak = _calculate_longest_streak(user)
    if longest_streak > stats.longest_streak:
        stats.longest_streak = longest_streak
    
    # Last activity date
    last_activity = completed_activities.order_by('-completed_at').first()
    if last_activity:
        stats.last_activity_date = last_activity.completed_at
    
    # Consistency rate (% of days with activity in last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    days_with_activity = completed_activities.filter(
        completed_at__gte=thirty_days_ago
    ).dates('completed_at', 'day').count()
    stats.consistency_rate = round((days_with_activity / 30) * 100, 2)
    
    # Update timestamp
    stats.last_updated = timezone.now()
    
    stats.save()


def _calculate_streak(user):
    """
    Calculate current consecutive days streak.
    A streak is broken if there's a day without any completed activity.
    """
    from django.utils import timezone
    from datetime import timedelta
    
    activities = Activity.objects.filter(
        user=user,
        completed=True
    ).order_by('-completed_at')
    
    if not activities.exists():
        return 0
    
    streak = 0
    current_date = timezone.now().date()
    
    # Get unique dates with activities
    activity_dates = set(
        activities.values_list('completed_at__date', flat=True)
    )
    
    # Check consecutive days from today backwards
    while current_date in activity_dates or (streak == 0 and current_date == timezone.now().date()):
        if current_date in activity_dates:
            streak += 1
        current_date -= timedelta(days=1)
        
        # If we're checking today and there's no activity yet, don't break streak
        if current_date == timezone.now().date() - timedelta(days=1) and streak == 0:
            current_date -= timedelta(days=1)
            continue
    
    return streak


def _calculate_longest_streak(user):
    """
    Calculate the longest consecutive days streak ever achieved.
    """
    from django.utils import timezone
    from datetime import timedelta
    
    activities = Activity.objects.filter(
        user=user,
        completed=True
    ).order_by('completed_at')
    
    if not activities.exists():
        return 0
    
    # Get unique dates with activities
    activity_dates = sorted(set(
        activities.values_list('completed_at__date', flat=True)
    ))
    
    if not activity_dates:
        return 0
    
    max_streak = 1
    current_streak = 1
    
    for i in range(1, len(activity_dates)):
        # Check if dates are consecutive
        if (activity_dates[i] - activity_dates[i-1]).days == 1:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 1
    
    return max_streak
