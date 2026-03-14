"""
Serializers for workout app API endpoints.
Used for request/response documentation and validation.
"""
from rest_framework import serializers
from workout.models import Program, Activity, WorkoutSession


class ActivitySerializer(serializers.ModelSerializer):
    """Serializer for Activity model"""
    activity_id = serializers.IntegerField(source='id', read_only=True, help_text="Activity ID")
    program_id = serializers.IntegerField(read_only=True, allow_null=True, help_text="Parent program ID")

    class Meta:
        model = Activity
        fields = [
            'activity_id', 'id', 'program_id', 'program', 'activity_name', 'activity_type', 'user_segment', 'rl_action_id',
            'description', 'duration_minutes', 'intensity', 'instructions',
            'duration_seconds',
            'assigned_date', 'completed', 'completion_date',
            'motivation_before', 'motivation_after', 'motivation_delta',
            'difficulty_rating', 'enjoyment_rating', 'is_motivating',
            'notes', 'engagement_contribution', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'motivation_delta', 'is_motivating',
            'engagement_contribution', 'created_at', 'updated_at'
        ]


class ProgramActivitySerializer(serializers.ModelSerializer):
    """Activity payload nested under a program."""
    activity_id = serializers.IntegerField(source='id', read_only=True, help_text="Activity ID")
    program_id = serializers.IntegerField(read_only=True, allow_null=True, help_text="Parent program ID")

    class Meta:
        model = Activity
        fields = [
            'activity_id', 'id', 'program_id', 'activity_name', 'activity_type', 'description',
            'duration_minutes', 'intensity', 'instructions',
            'duration_seconds',
            'completed', 'completion_date',
            'motivation_before', 'motivation_after',
            'assigned_date'
        ]
        read_only_fields = fields


class ProgramSerializer(serializers.ModelSerializer):
    """Program payload with contained activities."""
    program_id = serializers.IntegerField(source='id', read_only=True, help_text="Program ID")
    activities = ProgramActivitySerializer(many=True, read_only=True)
    total_activities = serializers.SerializerMethodField(help_text="Total activities in this program")
    completed_activities = serializers.SerializerMethodField(help_text="Number of completed activities")
    completion_rate = serializers.SerializerMethodField(help_text="Completion rate from 0.0 to 1.0")

    class Meta:
        model = Program
        fields = [
            'program_id', 'id', 'program_type', 'name', 'description', 'segment',
            'duration', 'frequency', 'intensity', 'progression', 'focus',
            'rl_action_id', 'completed', 'completion_date',
            'total_activities', 'completed_activities', 'completion_rate',
            'created_at', 'activities'
        ]
        read_only_fields = fields

    def get_total_activities(self, obj):
        return obj.activities.count()

    def get_completed_activities(self, obj):
        return obj.activities.filter(completed=True).count()

    def get_completion_rate(self, obj):
        total = obj.activities.count()
        if total == 0:
            return 0.0
        done = obj.activities.filter(completed=True).count()
        return round(done / total, 2)


class RecommendedProgramsResponseSerializer(serializers.Serializer):
    """Response for GET /workout/activity/recommended/ with persisted programs."""
    status = serializers.CharField(help_text="Success status")
    user_segment = serializers.CharField(help_text="User's wellness segment")
    activity_segment = serializers.CharField(help_text="Mapped activity catalog segment")
    rl_action = serializers.IntegerField(help_text="RL action ID selected (0-5)")
    rl_action_name = serializers.CharField(help_text="Human-readable action name")
    reason = serializers.CharField(help_text="Explanation of why these activities were chosen")
    physical_program = ProgramSerializer(help_text="Persisted physical program")
    mental_program = ProgramSerializer(help_text="Persisted mental program")
    total_activities = serializers.IntegerField(help_text="Number of created activities")
    user_engagement = serializers.FloatField(help_text="Current user engagement score (0-1)")
    user_motivation = serializers.IntegerField(help_text="Current user motivation score (1-5)")


class ActivityCompletionRequestSerializer(serializers.Serializer):
    """Request body for completing an activity"""
    completed = serializers.BooleanField(default=True, help_text="Whether the activity was completed")
    motivation = serializers.IntegerField(
        min_value=1, max_value=5, required=True,
        help_text="Your motivation level after completing the activity (1-5)"
    )


class ActivityCompletionResponseSerializer(serializers.Serializer):
    """Response for activity completion"""
    status = serializers.CharField()
    activity_id = serializers.IntegerField()
    activity_name = serializers.CharField()
    duration_minutes = serializers.IntegerField()
    duration_seconds = serializers.IntegerField()
    completed = serializers.BooleanField()
    motivation = serializers.IntegerField()
    engagement_contribution = serializers.FloatField()
    program_status = serializers.DictField(required=False, allow_null=True)
    user_stats = serializers.DictField()


class RecommendedActivitySerializer(serializers.Serializer):
    """Serializer for recommended activity in response"""
    activity_id = serializers.IntegerField(source='id', read_only=True, help_text="Activity ID")
    id = serializers.IntegerField(read_only=True, help_text="Activity ID")
    activity_name = serializers.CharField(help_text="Name of the activity")
    activity_type = serializers.CharField(help_text="Type: 'physical' or 'mental'")
    duration_minutes = serializers.IntegerField(help_text="Recommended duration in minutes")
    duration_seconds = serializers.IntegerField(help_text="Recommended duration in seconds")
    intensity = serializers.CharField(help_text="Intensity level: low, moderate, or high")
    instructions = serializers.CharField(help_text="Step-by-step instructions")
    user_segment = serializers.CharField(help_text="User segment this activity is for")
    rl_action_id = serializers.IntegerField(help_text="RL action ID (0-5)")
    assigned_date = serializers.DateField(help_text="Date assigned")
    completed = serializers.BooleanField(help_text="Whether activity is completed")
    description = serializers.CharField(required=False, help_text="Activity description")


class RecommendedActivitiesResponseSerializer(serializers.Serializer):
    """Response for GET /workout/activity/recommended/"""
    status = serializers.CharField(help_text="Success status")
    user_segment = serializers.CharField(help_text="User's wellness segment")
    rl_action = serializers.IntegerField(help_text="RL action ID selected (0-5)")
    rl_action_name = serializers.CharField(help_text="Human-readable action name")
    reason = serializers.CharField(help_text="Explanation of why these activities were chosen")
    recommended_activities = RecommendedActivitySerializer(many=True)
    total_activities = serializers.IntegerField(help_text="Number of activities recommended")
    user_engagement = serializers.FloatField(help_text="Current user engagement score (0-1)")
    user_motivation = serializers.IntegerField(help_text="Current user motivation score (1-5)")


class PhysicalProgramSerializer(serializers.Serializer):
    """Physical wellness program details"""
    name = serializers.CharField(help_text="Program name")
    description = serializers.CharField(help_text="Program description")
    exercises = serializers.ListField(child=serializers.CharField(), help_text="List of exercises")
    duration = serializers.CharField(help_text="Recommended duration")
    frequency = serializers.CharField(help_text="How often to do this program")
    intensity = serializers.CharField(help_text="Intensity level")
    progression = serializers.CharField(required=False, help_text="How to progress")


class MentalProgramSerializer(serializers.Serializer):
    """Mental wellness program details"""
    name = serializers.CharField(help_text="Program name")
    description = serializers.CharField(help_text="Program description")
    activities = serializers.ListField(child=serializers.CharField(), help_text="List of mental activities")
    duration = serializers.CharField(help_text="Recommended duration")
    frequency = serializers.CharField(help_text="How often to do this program")
    focus = serializers.CharField(help_text="Main focus area")


class RecommendProgramResponseSerializer(serializers.Serializer):
    """Response for GET /workout/recommend/"""
    user_segment = serializers.CharField(help_text="User's wellness segment classification")
    recommendation_type = serializers.CharField(help_text="Type of recommendation provided")
    rl_action = serializers.CharField(help_text="RL action applied to adapt the program")
    physical_program = PhysicalProgramSerializer(help_text="Physical wellness program")
    mental_program = MentalProgramSerializer(help_text="Mental wellness program")
    reminders = serializers.ListField(
        child=serializers.CharField(),
        help_text="Recommended reminders/notifications"
    )
    adaptation_reason = serializers.CharField(help_text="Why the RL agent adapted the program")
    engagement_score = serializers.FloatField(help_text="User's current engagement score (0-1)")
    motivation_score = serializers.IntegerField(help_text="User's current motivation score (1-5)")
    personalization_note = serializers.CharField(help_text="Note about personalization")
    next_steps = serializers.ListField(
        child=serializers.CharField(),
        help_text="Recommended next steps"
    )


class EngagementFeedbackRequestSerializer(serializers.Serializer):
    """Request body for engagement feedback"""
    engagement_delta = serializers.FloatField(
        min_value=-1, max_value=1,
        help_text="Change in engagement level (-1 to 1)"
    )
    workout_completed = serializers.BooleanField(
        default=False,
        help_text="Whether a workout was completed"
    )
    meditation_completed = serializers.BooleanField(
        default=False,
        help_text="Whether a meditation session was completed"
    )
    feedback_rating = serializers.IntegerField(
        min_value=1, max_value=5,
        help_text="Overall satisfaction rating (1-5)"
    )
    notes = serializers.CharField(
        max_length=500, required=False, allow_blank=True,
        help_text="Optional feedback notes"
    )


class EngagementFeedbackResponseSerializer(serializers.Serializer):
    """Response for engagement feedback submission"""
    status = serializers.CharField()
    message = serializers.CharField()
    user_metrics = serializers.DictField(help_text="Updated user metrics")
    training_metrics = serializers.DictField(help_text="RL training information")


class ActivityFeedbackItemSerializer(serializers.Serializer):
    """Individual activity feedback in batch"""
    activity_id = serializers.IntegerField(help_text="Activity ID")
    completed = serializers.BooleanField(help_text="Whether completed")
    motivation = serializers.IntegerField(
        min_value=1, max_value=5, required=True,
        help_text="Motivation level after activity (1-5)"
    )


class ActivityFeedbackBatchRequestSerializer(serializers.Serializer):
    """Request body for batch activity feedback"""
    activities = ActivityFeedbackItemSerializer(
        many=True,
        help_text="List of activities with feedback"
    )
    overall_session_rating = serializers.IntegerField(
        min_value=1, max_value=5,
        help_text="Overall session satisfaction (1-5)"
    )
    notes = serializers.CharField(
        max_length=1000, required=False, allow_blank=True,
        help_text="Optional session notes"
    )


class SessionMetricsSerializer(serializers.Serializer):
    """Session-level metrics"""
    completion_rate = serializers.FloatField()
    avg_motivation = serializers.FloatField()


class RLTrainingInfoSerializer(serializers.Serializer):
    """RL agent training information"""
    action_trained = serializers.IntegerField(help_text="Action that was trained")
    reward_signal = serializers.FloatField(help_text="Reward calculated from feedback")
    q_value_updated = serializers.BooleanField(help_text="Whether Q-table was updated")
    epsilon_current = serializers.FloatField(help_text="Current exploration rate")
    total_episodes = serializers.IntegerField(help_text="Total training episodes")
    total_reward = serializers.FloatField(help_text="Cumulative reward")


class ProgramUpdateSerializer(serializers.Serializer):
    """Program completion summary returned after activity updates."""
    program_id = serializers.IntegerField()
    total_activities = serializers.IntegerField()
    completed_activities = serializers.IntegerField()
    completion_rate = serializers.FloatField()
    completed = serializers.BooleanField()
    completion_date = serializers.DateTimeField(allow_null=True)


class ActivityFeedbackBatchResponseSerializer(serializers.Serializer):
    """Response for batch activity feedback"""
    status = serializers.CharField()
    session = serializers.DictField(help_text="Created workout session details")
    metrics = SessionMetricsSerializer(help_text="Session-level metrics")
    program_updates = ProgramUpdateSerializer(many=True, help_text="Updated program completion statuses")
    rl_training = RLTrainingInfoSerializer(help_text="RL training information")
    activity_recommendations = serializers.ListField(
        child=serializers.DictField(),
        help_text="Recommended activity modifications for future"
    )


class WorkoutSessionSerializer(serializers.ModelSerializer):
    """Serializer for WorkoutSession model"""
    
    class Meta:
        model = WorkoutSession
        fields = [
            'id', 'user', 'session_type', 'created_at', 'completed_at',
            'total_activities', 'completed_activities', 'completion_rate',
            'avg_motivation_before', 'avg_motivation_after', 'avg_motivation_delta',
            'total_duration_minutes', 'overall_session_rating', 'session_notes',
            'engagement_contribution'
        ]
        read_only_fields = [
            'id', 'created_at', 'total_activities', 'completed_activities',
            'completion_rate', 'avg_motivation_before', 'avg_motivation_after',
            'avg_motivation_delta', 'total_duration_minutes', 'engagement_contribution'
        ]
