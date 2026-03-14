from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer, UserStatisticsSerializer, StatisticsFilterSerializer
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Count, Avg, Sum, Q
from datetime import timedelta
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes


User = get_user_model()

@extend_schema(
    request=RegisterSerializer,
    responses={201:RegisterSerializer},
    description="Register new user",
)
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer


@extend_schema(
    tags=['Statistics'],
    parameters=[
        OpenApiParameter(
            name='period',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Time period: 7days, 30days, 90days, all, or custom',
            enum=['7days', '30days', '90days', 'all', 'custom'],
        ),
        OpenApiParameter(
            name='start_date',
            type=OpenApiTypes.DATETIME,
            location=OpenApiParameter.QUERY,
            description='Start date for custom period (ISO format)',
            required=False,
        ),
        OpenApiParameter(
            name='end_date',
            type=OpenApiTypes.DATETIME,
            location=OpenApiParameter.QUERY,
            description='End date for custom period (ISO format)',
            required=False,
        ),
    ],
    responses={200: UserStatisticsSerializer},
    description="Get comprehensive user statistics with filtering options. Returns structured data for frontend graphs and visualizations."
)
class UserStatisticsView(APIView):
    """
    Comprehensive user statistics endpoint with flexible filtering.
    
    Provides:
    - Activity counts and breakdowns
    - Time series data for graphing
    - Motivation and engagement trends
    - Performance ratings
    - Goal progress tracking
    - Streak information
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Import here to avoid circular imports
        from workout.models import Activity, WorkoutSession
        
        # Validate filters
        filter_serializer = StatisticsFilterSerializer(data=request.query_params)
        if not filter_serializer.is_valid():
            return Response(
                filter_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        filters = filter_serializer.validated_data
        user = request.user
        
        # Determine date range
        end_date = timezone.now()
        period = filters['period']
        
        if period == 'custom':
            start_date = filters['start_date']
            end_date = filters['end_date']
        elif period == '7days':
            start_date = end_date - timedelta(days=7)
        elif period == '30days':
            start_date = end_date - timedelta(days=30)
        elif period == '90days':
            start_date = end_date - timedelta(days=90)
        else:  # 'all'
            start_date = user.date_joined
        
        # Base queryset for activities in the period
        activities = Activity.objects.filter(user=user)
        period_activities = activities.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        completed_activities = period_activities.filter(completed=True)
        
        # 1. OVERVIEW METRICS
        total_completed = completed_activities.count()
        total_assigned = period_activities.count()
        completion_rate = (total_completed / total_assigned * 100) if total_assigned > 0 else 0
        
        total_duration = completed_activities.aggregate(
            total=Sum('duration_minutes')
        )['total'] or 0
        
        overview = {
            'total_activities_completed': total_completed,
            'total_activities_assigned': total_assigned,
            'completion_rate': round(completion_rate, 1),
            'total_duration_minutes': total_duration,
            'total_duration_hours': round(total_duration / 60, 1),
        }
        
        # 2. ACTIVITY BREAKDOWN BY TYPE
        activity_breakdown = {
            'exercise': completed_activities.filter(activity_type='exercise').count(),
            'meditation': completed_activities.filter(activity_type='meditation').count(),
            'journaling': completed_activities.filter(activity_type='journaling').count(),
        }
        
        # Duration breakdown by type
        duration_by_type = {}
        for act_type in ['exercise', 'meditation', 'journaling']:
            duration = completed_activities.filter(activity_type=act_type).aggregate(
                total=Sum('duration_minutes')
            )['total'] or 0
            duration_by_type[act_type] = duration
        
        # 3. DAILY TIME SERIES DATA
        daily_activity_count = []
        daily_duration = []
        
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        while current_date <= end_date_only:
            next_date = current_date + timedelta(days=1)
            
            day_activities = completed_activities.filter(
                completion_date__date=current_date
            )
            
            count = day_activities.count()
            duration = day_activities.aggregate(total=Sum('duration_minutes'))['total'] or 0
            
            daily_activity_count.append({
                'date': current_date.isoformat(),
                'count': count,
                'exercise': day_activities.filter(activity_type='exercise').count(),
                'meditation': day_activities.filter(activity_type='meditation').count(),
                'journaling': day_activities.filter(activity_type='journaling').count(),
            })
            
            daily_duration.append({
                'date': current_date.isoformat(),
                'total_minutes': duration,
                'exercise_minutes': day_activities.filter(activity_type='exercise').aggregate(
                    total=Sum('duration_minutes')
                )['total'] or 0,
                'meditation_minutes': day_activities.filter(activity_type='meditation').aggregate(
                    total=Sum('duration_minutes')
                )['total'] or 0,
            })
            
            current_date = next_date
        
        # 4. MOTIVATION TRENDS
        motivation_data = completed_activities.filter(
            motivation_before__isnull=False,
            motivation_after__isnull=False
        ).aggregate(
            avg_before=Avg('motivation_before'),
            avg_after=Avg('motivation_after'),
            avg_delta=Avg('motivation_delta'),
        )
        
        motivation_trends = {
            'average_motivation_before': round(motivation_data['avg_before'] or 0, 2),
            'average_motivation_after': round(motivation_data['avg_after'] or 0, 2),
            'average_improvement': round(motivation_data['avg_delta'] or 0, 2),
            'activities_with_improvement': completed_activities.filter(is_motivating=True).count(),
            'improvement_rate': round(
                (completed_activities.filter(is_motivating=True).count() / total_completed * 100)
                if total_completed > 0 else 0,
                1
            ),
        }
        
        # 5. ENGAGEMENT METRICS
        # Calculate current streak
        current_streak = self._calculate_streak(user, activities)
        
        # Get workout sessions in period
        sessions = WorkoutSession.objects.filter(
            user=user,
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        engagement = {
            'current_streak_days': current_streak,
            'total_sessions': sessions.count(),
            'avg_session_completion_rate': round(
                sessions.aggregate(avg=Avg('completion_rate'))['avg'] or 0,
                1
            ),
            'engagement_score': round(user.engagement_score, 2),
            'motivation_score': user.motivation_score,
        }
        
        # 6. PERFORMANCE RATINGS
        ratings_data = completed_activities.aggregate(
            avg_enjoyment=Avg('enjoyment_rating'),
            avg_difficulty=Avg('difficulty_rating'),
        )
        
        ratings = {
            'average_enjoyment': round(ratings_data['avg_enjoyment'] or 0, 2),
            'average_difficulty': round(ratings_data['avg_difficulty'] or 0, 2),
            'highly_enjoyed_activities': completed_activities.filter(
                enjoyment_rating__gte=4
            ).count(),
            'well_balanced_activities': completed_activities.filter(
                difficulty_rating__in=[2, 3]  # Not too easy, not too hard
            ).count(),
        }
        
        # 7. GOAL PROGRESS
        days_in_period = (end_date - start_date).days
        weeks_in_period = max(days_in_period / 7, 1)
        
        goal_progress = {
            'average_activities_per_week': round(total_completed / weeks_in_period, 1),
            'total_workouts_lifetime': user.workouts_completed,
            'total_meditations_lifetime': user.meditation_sessions,
        }
        
        # 8. RECENT ACTIVITIES (Last 5)
        recent_activities = []
        for activity in completed_activities.order_by('-completion_date')[:5]:
            recent_activities.append({
                'id': activity.id,
                'name': activity.activity_name,
                'type': activity.activity_type,
                'completed_date': activity.completion_date.isoformat() if activity.completion_date else None,
                'duration_minutes': activity.duration_minutes,
                'motivation_delta': activity.motivation_delta,
                'enjoyment_rating': activity.enjoyment_rating,
            })
        
        # Compile response
        response_data = {
            'period': period,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'overview': overview,
            'activity_breakdown': {
                **activity_breakdown,
                'duration_by_type': duration_by_type,
            },
            'daily_activity_count': daily_activity_count,
            'daily_duration': daily_duration,
            'motivation_trends': motivation_trends,
            'engagement': engagement,
            'ratings': ratings,
            'goal_progress': goal_progress,
            'recent_activities': recent_activities,
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    def _calculate_streak(self, user, activities_queryset):
        """Calculate current activity streak in days."""
        today = timezone.now().date()
        current_streak = 0
        check_date = today
        
        # Look back up to 365 days for streak
        for _ in range(365):
            has_activity = activities_queryset.filter(
                completed=True,
                completion_date__date=check_date
            ).exists()
            
            if has_activity:
                current_streak += 1
                check_date -= timedelta(days=1)
            else:
                # Allow one day grace period (if checking today or yesterday)
                if check_date == today:
                    check_date -= timedelta(days=1)
                    continue
                break
        
        return current_streak
