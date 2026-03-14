from django.urls import path 
from .views import (
    RecommendProgram, 
    EngagementFeedback,
    RecommendedActivitiesView,
    ProgramListView,
    ProgramDetailView,
    ActivityDetailView,
    CompleteActivityView,
    ActivityFeedbackBatchView
)


app_name = 'workout'
urlpatterns=[
    path('recommend/', RecommendProgram.as_view(), name='recommend_program'),
    path('feedback/', EngagementFeedback.as_view(), name='engagement_feedback'),
    path('activity/recommended/', RecommendedActivitiesView.as_view(), name='recommended_activities'),
    path('programs/', ProgramListView.as_view(), name='program_list'),
    path('programs/<int:program_id>/', ProgramDetailView.as_view(), name='program_detail'),
    path('activity/<int:activity_id>/', ActivityDetailView.as_view(), name='activity_detail'),
    path('activity/<int:activity_id>/complete/', CompleteActivityView.as_view(), name='complete_activity'),
    path('activity/feedback-batch/', ActivityFeedbackBatchView.as_view(), name='activity_feedback_batch'),
]