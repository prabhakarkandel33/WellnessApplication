from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser,UserStatistics


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'age', 'gender', 'stress_level', 'mental_health_condition', 'happiness_score', 'engagement_score']
    list_filter = ['gender', 'stress_level', 'mental_health_condition', 'diet_type', 'is_staff', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Personal Information', {
            'fields': ('age', 'gender')
        }),
        ('Health & Wellness Profile', {
            'fields': ('diet_type', 'stress_level', 'mental_health_condition', 'exercise_level',
                      'sleep_hours', 'happiness_score', 'self_reported_social_interaction_score')
        }),
        ('Lifestyle Metrics', {
            'fields': ('work_hours_per_week', 'screen_time_per_day', 'segment_label')
        }),
        ('Goals', {
            'fields': ('primary_goal', 'workout_goal_days')
        }),
        ('RL Agent Metrics', {
            'fields': ('engagement_score', 'motivation_score', 'workouts_completed', 'meditation_sessions', 
                      'last_action_recommended', 'last_recommendation_date'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserStatistics)
class UserStatisticsAdmin(admin.ModelAdmin):
    list_display = [
        'user', 
        'total_activities_completed', 
        'current_streak_days',
        'activities_this_week',
        'overall_completion_rate',
        'last_activity_date'
    ]
    list_filter = ['last_activity_date']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'last_updated']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Activity Counts', {
            'fields': ('total_activities_completed', 'total_activities_assigned', 'total_exercises', 
                      'total_meditations', 'total_journaling')
        }),
        ('Engagement', {
            'fields': ('current_streak_days', 'longest_streak_days', 'last_activity_date')
        }),
        ('Performance', {
            'fields': ('avg_motivation_improvement', 'avg_enjoyment_rating', 'avg_difficulty_rating',
                      'overall_completion_rate')
        }),
        ('Time Metrics', {
            'fields': ('total_minutes_exercised', 'total_minutes_meditated')
        }),
        ('Periodic Stats', {
            'fields': ('activities_this_week', 'minutes_this_week', 'activities_this_month', 'minutes_this_month')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'last_updated'),
            'classes': ('collapse',)
        }),
    )