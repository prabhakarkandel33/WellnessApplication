from django.contrib import admin
from .models import Activity, WorkoutSession


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ['activity_name', 'user', 'activity_type', 'completed', 'motivation_delta', 'engagement_contribution', 'created_at']
    list_filter = ['activity_type', 'completed', 'intensity', 'user_segment']
    search_fields = ['activity_name', 'user__username', 'description']
    readonly_fields = ['motivation_delta', 'is_motivating', 'created_at', 'updated_at']
    
    fieldsets = (
        ('User & Context', {
            'fields': ('user', 'user_segment', 'rl_action_id')
        }),
        ('Activity Details', {
            'fields': ('activity_name', 'activity_type', 'description', 'duration_minutes', 'intensity', 'instructions')
        }),
        ('Timeline', {
            'fields': ('assigned_date', 'completed', 'completion_date')
        }),
        ('User Feedback', {
            'fields': ('motivation_before', 'motivation_after', 'difficulty_rating', 'enjoyment_rating', 'notes')
        }),
        ('Calculated Metrics', {
            'fields': ('motivation_delta', 'is_motivating'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(WorkoutSession)
class WorkoutSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'session_type', 'created_at', 'completion_rate', 'avg_motivation_delta', 'overall_session_rating']
    list_filter = ['session_type', 'overall_session_rating', 'created_at']
    search_fields = ['user__username', 'notes']
    readonly_fields = ['completion_rate', 'avg_motivation_before', 'avg_motivation_after', 'avg_motivation_delta', 
                       'total_activities', 'completed_activities', 'total_duration_minutes', 'created_at', 'completed_at']
    filter_horizontal = ['activities']
    
    fieldsets = (
        ('User & Session', {
            'fields': ('user', 'session_type', 'overall_session_rating', 'session_notes', 'created_at', 'completed_at')
        }),
        ('Activities', {
            'fields': ('activities',)
        }),
        ('Calculated Metrics', {
            'fields': ('total_activities', 'completed_activities', 'completion_rate', 'avg_motivation_before', 
                      'avg_motivation_after', 'avg_motivation_delta', 'total_duration_minutes'),
            'classes': ('collapse',)
        }),
    )
