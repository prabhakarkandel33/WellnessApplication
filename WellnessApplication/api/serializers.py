from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
import joblib
import os
from django.conf import settings
import numpy as np

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'email', 'username', 'password', 'password2',
            'age', 'gender', 'height', 'weight',
            'self_reported_stress', 'gad7_score',
            'physical_activity_week', 'importance_stress_reduction',
            'primary_goal', 'workout_goal_days',
            'segment_label'
        ]
        extra_kwargs = {
            'segment_label': {'read_only': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords don't match"})
        return attrs

    def validate_age(self, value):
        if not 1 <= value <= 100:
            raise serializers.ValidationError("Age must be between 1 and 100.")
        return value

    def validate_self_reported_stress(self, value):
        if not 1 <= value <= 10:
            raise serializers.ValidationError("Stress level must be between 1 and 10.")
        return value

    def validate_gad7_score(self, value):
        if not 0 <= value <= 21:
            raise serializers.ValidationError("GAD-7 score must be between 0 and 21.")
        return value

    def validate_physical_activity_week(self, value):
        if not 0 <= value <= 7:
            raise serializers.ValidationError("Physical activity must be between 0 and 7 days/week.")
        return value

    def validate_importance_stress_reduction(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Importance of stress reduction must be between 1 and 5.")
        return value

    def validate_workout_goal_days(self, value):
        if not 0 <= value <= 7:
            raise serializers.ValidationError("Workout goal days must be between 0 and 7.")
        return value

    def create(self, validated_data):
        validated_data.pop('password2')

        # --- Load model ---
        model_path = os.path.join(settings.BASE_DIR, 'Datasets,Models', 'segment_classifier.pkl')
        clf = joblib.load(model_path)

        # --- Calculate derived features ---
        gender = validated_data.get('gender')
        gender_encoded = 0 if gender == 'male' else 1

        height_cm = validated_data.get('height', 0.0)
        weight_kg = validated_data.get('weight', 0.0)

        # Avoid division by zero
        height_m = height_cm / 100 if height_cm else 1
        bmi = weight_kg / (height_m ** 2)

        # --- Prepare feature vector in trained order ---
        features = np.array([[
            validated_data.get('age', 0),
            gender_encoded,
            height_cm,
            weight_kg,
            bmi,
            validated_data.get('gad7_score', 0),
            validated_data.get('self_reported_stress', 5),
            validated_data.get('physical_activity_week', 0),
            validated_data.get('primary_goal', 0),
            validated_data.get('workout_goal_days', 0),
            validated_data.get('importance_stress_reduction', 3)
        ]])

        # --- Predict segment label ---
        segment_label = int(clf.predict(features)[0])
        validated_data['segment_label'] = segment_label

        # --- Create user ---
        user = User.objects.create_user(**validated_data)
        return user

class UserStatisticsSerializer(serializers.Serializer):
    """
    Comprehensive statistics response for frontend visualization.
    All data structured for easy graphing and display.
    """
    # Filter info
    period = serializers.CharField()
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    
    # Overview metrics
    overview = serializers.DictField(child=serializers.JSONField())
    
    # Activity breakdown by type
    activity_breakdown = serializers.DictField(child=serializers.IntegerField())
    
    # Time series data for graphs
    daily_activity_count = serializers.ListField(child=serializers.DictField())
    daily_duration = serializers.ListField(child=serializers.DictField())
    
    # Motivation trends
    motivation_trends = serializers.DictField(child=serializers.JSONField())
    
    # Engagement metrics
    engagement = serializers.DictField(child=serializers.JSONField())
    
    # Performance ratings
    ratings = serializers.DictField(child=serializers.JSONField())
    
    # Goal progress
    goal_progress = serializers.DictField(child=serializers.JSONField())
    
    # Recent activities summary
    recent_activities = serializers.ListField(child=serializers.DictField())


class StatisticsFilterSerializer(serializers.Serializer):
    """
    Request serializer for filtering statistics.
    """
    PERIOD_CHOICES = [
        ('7days', 'Last 7 Days'),
        ('30days', 'Last 30 Days'),
        ('90days', 'Last 90 Days'),
        ('all', 'All Time'),
        ('custom', 'Custom Range'),
    ]
    
    period = serializers.ChoiceField(choices=PERIOD_CHOICES, default='30days')
    start_date = serializers.DateTimeField(required=False, allow_null=True)
    end_date = serializers.DateTimeField(required=False, allow_null=True)
    
    def validate(self, data):
        if data['period'] == 'custom':
            if not data.get('start_date') or not data.get('end_date'):
                raise serializers.ValidationError(
                    "start_date and end_date are required for custom period"
                )
            if data['start_date'] >= data['end_date']:
                raise serializers.ValidationError(
                    "start_date must be before end_date"
                )
        return data