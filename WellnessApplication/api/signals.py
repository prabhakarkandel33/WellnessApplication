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
    from django.db.models import Sum, Avg
    from django.utils import timezone
    from datetime import timedelta

    # Get or create statistics object
    stats, _ = UserStatistics.objects.get_or_create(user=user)

    all_activities = Activity.objects.filter(user=user)
    completed_activities = all_activities.filter(completed=True)

    # Core activity counts
    stats.total_activities_completed = completed_activities.count()

    # By-type completion counts
    stats.total_exercises = completed_activities.filter(activity_type='exercise').count()
    stats.total_meditations = completed_activities.filter(activity_type='meditation').count()
    stats.total_journaling = completed_activities.filter(activity_type='journaling').count()

    # Time metrics by type
    stats.total_minutes_exercised = (
        completed_activities.filter(activity_type='exercise').aggregate(total=Sum('duration_minutes'))['total'] or 0
    )
    stats.total_minutes_meditated = (
        completed_activities.filter(activity_type='meditation').aggregate(total=Sum('duration_minutes'))['total'] or 0
    )

    # Averages
    stats.avg_motivation_improvement = round(
        completed_activities.exclude(motivation_delta__isnull=True).aggregate(avg=Avg('motivation_delta'))['avg'] or 0.0,
        2,
    )
    stats.avg_enjoyment_rating = round(
        completed_activities.exclude(enjoyment_rating__isnull=True).aggregate(avg=Avg('enjoyment_rating'))['avg'] or 0.0,
        2,
    )
    stats.avg_difficulty_rating = round(
        completed_activities.exclude(difficulty_rating__isnull=True).aggregate(avg=Avg('difficulty_rating'))['avg'] or 0.0,
        2,
    )

    # Completion rate (% assigned that were completed)
    stats.total_activities_assigned = all_activities.count()
    if stats.total_activities_assigned > 0:
        stats.overall_completion_rate = round(
            (stats.total_activities_completed / stats.total_activities_assigned) * 100.0,
            2,
        )
    else:
        stats.overall_completion_rate = 0.0

    # Weekly and monthly rolling windows
    now = timezone.now()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    week_activities = completed_activities.filter(completion_date__gte=week_ago)
    month_activities = completed_activities.filter(completion_date__gte=month_ago)

    stats.activities_this_week = week_activities.count()
    stats.minutes_this_week = week_activities.aggregate(total=Sum('duration_minutes'))['total'] or 0
    stats.activities_this_month = month_activities.count()
    stats.minutes_this_month = month_activities.aggregate(total=Sum('duration_minutes'))['total'] or 0

    # Streak metrics
    stats.current_streak_days = _calculate_streak(user)
    stats.longest_streak_days = _calculate_longest_streak(user)

    # Last completed activity date
    last_activity = completed_activities.order_by('-completion_date').first()
    if last_activity:
        stats.last_activity_date = last_activity.completion_date.date() if last_activity.completion_date else None

    stats.save()


def _calculate_streak(user):
    """
    Calculate current consecutive days streak.
    A streak is broken if there's a day without any completed activity.
    """
    from django.utils import timezone
    from datetime import timedelta

    activity_dates = set(
        Activity.objects.filter(
            user=user,
            completed=True,
            completion_date__isnull=False,
        ).values_list('completion_date__date', flat=True)
    )

    if not activity_dates:
        return 0

    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    start_date = today if today in activity_dates else (yesterday if yesterday in activity_dates else None)

    if start_date is None:
        return 0

    streak = 0
    current_date = start_date
    while current_date in activity_dates:
        streak += 1
        current_date -= timedelta(days=1)

    return streak


def _calculate_longest_streak(user):
    """
    Calculate the longest consecutive days streak ever achieved.
    """
    activity_dates = sorted(set(
        Activity.objects.filter(
        user=user,
            completed=True,
            completion_date__isnull=False,
        ).values_list('completion_date__date', flat=True)
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
