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
            'age', 'gender', 'diet_type', 'stress_level',
            'mental_health_condition', 'exercise_level', 'sleep_hours', 
            'work_hours_per_week', 'screen_time_per_day', 
            'self_reported_social_interaction_score', 'happiness_score', 
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

    def validate_sleep_hours(self, value):
        if not 0 <= value <= 9:
            raise serializers.ValidationError("Sleep hours must be between 0 and 9.")
        return value

    def validate_work_hours_per_week(self, value):
        if not 0 <= value <= 100:
            raise serializers.ValidationError("Work hours per week must be between 0 and 100.")
        return value

    def validate_screen_time_per_day(self, value):
        if not 0 <= value <= 24:
            raise serializers.ValidationError("Screen time must be between 0 and 24 hours.")
        return value

    def validate_self_reported_social_interaction_score(self, value):
        if not 0 <= value <= 10:
            raise serializers.ValidationError("Social interaction score must be between 0 and 10.")
        return value

    def validate_happiness_score(self, value):
        if not 0 <= value <= 10:
            raise serializers.ValidationError("Happiness score must be between 0 and 10.")
        return value

    def create(self, validated_data):
        validated_data.pop('password2')

        # --- Load Random Forest model ---
        model_path = os.path.join(settings.BASE_DIR, 'Datasets,Models', 'final_RF.pkl')
        rf_model = joblib.load(model_path)

        # --- Encode categorical features (must match training order) ---
        # Feature order: Age, Gender, Exercise Level, Diet Type, Sleep Hours, 
        # Stress Level, Mental Health Condition, Work Hours per Week, 
        # Screen Time per Day (Hours), Social Interaction Score, Happiness Score
        
        gender = validated_data.get('gender', 'male')
        gender_mapping = {'male': 0, 'female': 1, 'other': 2}
        gender_encoded = gender_mapping.get(gender, 0)
        
        exercise_level = validated_data.get('exercise_level', 'moderate')
        exercise_mapping = {'low': 0, 'moderate': 1, 'high': 2}
        exercise_encoded = exercise_mapping.get(exercise_level, 1)
        
        diet_type = validated_data.get('diet_type', 'balanced')
        diet_mapping = {'vegetarian': 0, 'vegan': 1, 'balanced': 2, 'junk_food': 3, 'keto': 4}
        diet_encoded = diet_mapping.get(diet_type, 2)
        
        stress_level = validated_data.get('stress_level', 'moderate')
        stress_mapping = {'low': 0, 'moderate': 1, 'high': 2}
        stress_encoded = stress_mapping.get(stress_level, 1)
        
        mental_health = validated_data.get('mental_health_condition', 'none')
        mental_mapping = {'none': 0, 'ptsd': 1, 'depression': 2, 'anxiety': 3, 'bipolar': 4}
        mental_encoded = mental_mapping.get(mental_health, 0)

        # --- Prepare feature vector (11 features in exact training order) ---
        features = np.array([[
            validated_data.get('age', 25),
            gender_encoded,
            exercise_encoded,
            diet_encoded,
            validated_data.get('sleep_hours', 7),
            stress_encoded,
            mental_encoded,
            validated_data.get('work_hours_per_week', 40),
            validated_data.get('screen_time_per_day', 6.0),
            validated_data.get('self_reported_social_interaction_score', 5),
            validated_data.get('happiness_score', 5)
        ]])

        # --- Predict segment label using Random Forest ---
        segment_prediction = rf_model.predict(features)[0]
        
        # Map string label back to numeric cluster ID
        label_to_id_mapping = {
            'Older_HighStress_Exhausted': 0,
            'Young_HighStress_ActiveSocial': 1,
            'MidLife_LowStress_Depressed': 2,
            'MidLife_Thriving_WellnessSeeker': 3,
            'WorkingProfessional_Sedentary_Stable': 4
        }
        
        # If prediction is already numeric (shouldn't be), use it directly
        # Otherwise map the string label to its numeric ID
        if isinstance(segment_prediction, (int, np.integer)):
            segment_label = int(segment_prediction)
        else:
            segment_label = label_to_id_mapping.get(segment_prediction, 4)  # Default to 4 if unknown
        
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