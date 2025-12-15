from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'age', 'gender', 'gad7_score', 'physical_activity_week', 'engagement_score', 'motivation_score']
    list_filter = ['gender', 'is_staff', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Health Profile', {
            'fields': ('age', 'gender', 'height', 'weight', 'gad7_score', 'physical_activity_week', 'segment_label')
        }),
        ('RL Agent Metrics', {
            'fields': ('engagement_score', 'motivation_score', 'workouts_completed', 'meditation_sessions', 
                      'last_action_recommended', 'last_recommendation_date'),
            'classes': ('collapse',)
        }),
    )