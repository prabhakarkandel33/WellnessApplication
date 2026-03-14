from django.shortcuts import render
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from django.db.models import Avg, Sum, Count
import re
import random
import os
import sys

# Add parent directory to path to import from api
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.rl_agent import WellnessRLAgent, RLModelManager
from workout.models import Program, Activity, WorkoutSession
from workout.activities import ACTIVITIES_BY_SEGMENT
from workout.serializers import (
    RecommendProgramResponseSerializer,
    EngagementFeedbackRequestSerializer,
    EngagementFeedbackResponseSerializer,
    RecommendedProgramsResponseSerializer,
    ActivitySerializer,
    ActivityCompletionRequestSerializer,
    ActivityCompletionResponseSerializer,
    ActivityFeedbackBatchRequestSerializer,
    ActivityFeedbackBatchResponseSerializer,
    ProgramFeedbackRequestSerializer,
    ProgramSerializer,
)


SEGMENT_TO_ACTIVITY_KEY = {
    "Older High Stress Exhausted": "High Anxiety, Low Activity",
    "Young High Stress Active Social": "Low Anxiety, High Activity",
    "Mid Life Low Stress Depressed": "Physical Health Risk",
    "Mid Life Thriving Wellness Seeker": "Moderate Anxiety, Moderate Activity",
    "Working Professional Sedentary Stable": "Moderate Anxiety, Moderate Activity",
}


def get_activity_segment_key(segment_name):
    """Map model segment labels to activity-catalog segment keys."""
    return SEGMENT_TO_ACTIVITY_KEY.get(segment_name, "Moderate Anxiety, Moderate Activity")


def safe_int_or_default(value, default, min_value=None, max_value=None):
    """Coerce a value to int while tolerating None/invalid input."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = int(default)

    if min_value is not None:
        number = max(min_value, number)
    if max_value is not None:
        number = min(max_value, number)
    return number


def safe_float_or_default(value, default, min_value=None, max_value=None):
    """Coerce a value to float while tolerating None/invalid input."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = float(default)

    if min_value is not None:
        number = max(min_value, number)
    if max_value is not None:
        number = min(max_value, number)
    return number


def sync_program_completion(program):
    """Update program completion state based on contained activities."""
    if program is None:
        return None

    total = program.activities.count()
    done = program.activities.filter(completed=True).count()
    should_complete = total > 0 and done == total

    updates = []
    if program.completed != should_complete:
        program.completed = should_complete
        updates.append('completed')

    if should_complete and program.completion_date is None:
        program.completion_date = timezone.now()
        updates.append('completion_date')

    if (not should_complete) and program.completion_date is not None:
        program.completion_date = None
        updates.append('completion_date')

    if updates:
        program.save(update_fields=updates)

    return {
        'program_id': program.id,
        'total_activities': total,
        'completed_activities': done,
        'completion_rate': round(done / total, 2) if total else 0.0,
        'completed': should_complete,
        'completion_date': program.completion_date.isoformat() if program.completion_date else None,
    }

@extend_schema(tags=['Workout Programs'])
class RecommendProgram(APIView):
    """
    View to recommend a workout program based on user profile.
    Uses RL agent to adapt recommendations based on user engagement.
    """
    permission_classes = [IsAuthenticated]
    
    # RL Agent instance and model manager (class-level for persistence across requests)
    rl_model_manager = RLModelManager(model_dir='api/models')
    rl_agent = None
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Load RL agent on first initialization
        if RecommendProgram.rl_agent is None:
            RecommendProgram.rl_agent = RecommendProgram.rl_model_manager.load_agent()
        
        # Baseline program recommendations from Table 4.1 in the report
        self.program_recommendations = {
            "Older High Stress Exhausted": {
                "physical_program": {
                    "name": "Light Yoga & Stretching Program",
                    "description": "Gentle movements to build activity habits",
                    "exercises": [
                        "Basic stretching routine",
                        "Light yoga poses (Child's pose, Cat-cow, Mountain pose)",
                        "Breathing-focused movements"
                    ],
                    "duration": "20-25 minutes",
                    "frequency": "2-3 times per week",
                    "intensity": "Low",
                    "progression": "Start with 2 days, gradually increase to 3"
                },
                "mental_program": {
                    "name": "Daily Mindfulness & Breathing",
                    "description": "Structured anxiety reduction through meditation",
                    "activities": [
                        "Guided meditation sessions",
                        "Deep breathing exercises (4-7-8 technique)",
                        "Progressive muscle relaxation"
                    ],
                    "duration": "10-15 minutes daily",
                    "frequency": "Daily",
                    "focus": "Anxiety reduction and stress management"
                },
                "reminders": [
                    "Gentle evening meditation reminder",
                    "Morning breathing exercise prompt",
                    "Weekly progress check-in"
                ]
            },
            
            "Working Professional Sedentary Stable": {
                "physical_program": {
                    "name": "Walk + Bodyweight Training",
                    "description": "Balanced approach combining cardio and strength",
                    "exercises": [
                        "Brisk walking (20-30 minutes)",
                        "Bodyweight exercises (push-ups, squats, planks)",
                        "Light resistance movements"
                    ],
                    "duration": "30-40 minutes",
                    "frequency": "3-4 times per week",
                    "intensity": "Moderate",
                    "progression": "Increase duration and add more bodyweight exercises"
                },
                "mental_program": {
                    "name": "CBT-based Journaling + Mindfulness",
                    "description": "Cognitive behavioral techniques with mindfulness",
                    "activities": [
                        "Daily mood and thought journaling",
                        "Weekly structured mindfulness sessions",
                        "Gratitude practice"
                    ],
                    "duration": "15-20 minutes",
                    "frequency": "Daily journaling, 2-3x weekly meditation",
                    "focus": "Thought pattern awareness and emotional regulation"
                },
                "reminders": [
                    "Evening journaling prompt",
                    "Mid-week mindfulness session",
                    "Progress celebration messages"
                ]
            },
            
            "Young High Stress Active Social": {
                "physical_program": {
                    "name": "Personalized Strength & Cardio Training",
                    "description": "Advanced training for active individuals",
                    "exercises": [
                        "Structured strength training routines",
                        "High-intensity cardio sessions",
                        "Sport-specific movements"
                    ],
                    "duration": "45-60 minutes",
                    "frequency": "5-6 times per week",
                    "intensity": "High",
                    "progression": "Progressive overload and periodization"
                },
                "mental_program": {
                    "name": "Light Breathing & Productivity Planning",
                    "description": "Minimal mental health maintenance for balanced individuals",
                    "activities": [
                        "Quick breathing exercises",
                        "Weekly goal setting sessions",
                        "Performance mindfulness"
                    ],
                    "duration": "5-10 minutes",
                    "frequency": "As needed",
                    "focus": "Performance optimization and stress prevention"
                },
                "reminders": [
                    "Pre-workout breathing exercise",
                    "Weekly goal review",
                    "Recovery day reminders"
                ]
            },
            
            "Mid Life Low Stress Depressed": {
                "physical_program": {
                    "name": "Beginner Bodyweight & Cardio",
                    "description": "Health-focused gradual fitness improvement",
                    "exercises": [
                        "Low-impact cardio (walking, swimming)",
                        "Basic bodyweight movements",
                        "Flexibility and mobility work"
                    ],
                    "duration": "20-30 minutes",
                    "frequency": "3-5 times per week",
                    "intensity": "Low to moderate",
                    "progression": "Very gradual increase in duration and intensity"
                },
                "mental_program": {
                    "name": "Motivation & Habit Tracking",
                    "description": "Building sustainable healthy habits",
                    "activities": [
                        "Daily habit tracking",
                        "Motivational content delivery",
                        "Short breathing routines"
                    ],
                    "duration": "10-15 minutes",
                    "frequency": "Daily tracking, 3x weekly breathing",
                    "focus": "Habit formation and motivation maintenance"
                },
                "reminders": [
                    "Daily habit check-in",
                    "Motivational quotes",
                    "Health milestone celebrations"
                ]
            },
            
            "Mid Life Thriving Wellness Seeker": {
                "physical_program": {
                    "name": "Balanced Yoga + Cardio + Strength",
                    "description": "Holistic approach to physical wellness",
                    "exercises": [
                        "Vinyasa yoga flows",
                        "Moderate cardio sessions",
                        "Functional strength training"
                    ],
                    "duration": "35-45 minutes",
                    "frequency": "4-5 times per week",
                    "intensity": "Moderate",
                    "progression": "Balanced progression across all fitness domains"
                },
                "mental_program": {
                    "name": "Journaling + Meditation + Gratitude",
                    "description": "Comprehensive mental wellness approach",
                    "activities": [
                        "Daily gratitude journaling",
                        "Guided meditation sessions",
                        "Weekly reflection practices"
                    ],
                    "duration": "20-25 minutes",
                    "frequency": "Daily",
                    "focus": "Holistic mental wellness and personal growth"
                },
                "reminders": [
                    "Morning gratitude prompt",
                    "Evening meditation reminder",
                    "Weekly wellness check-in"
                ]
            }
        }

    def get_user_state_dict(self, user):
        """
        Extract user state dictionary from user object for RL agent
        """
        # Encode categorical fields
        gender_mapping = {'male': 0, 'female': 1, 'other': 2}
        gender_encoded = gender_mapping.get(user.gender, 0) if user.gender else 0
        
        diet_mapping = {'vegetarian': 0, 'vegan': 1, 'balanced': 2, 'junk_food': 3, 'keto': 4}
        diet_encoded = diet_mapping.get(user.diet_type, 2) if user.diet_type else 2
        
        exercise_mapping = {'low': 0, 'moderate': 1, 'high': 2}
        exercise_encoded = exercise_mapping.get(user.exercise_level, 1) if user.exercise_level else 1
        
        stress_mapping = {'low': 0, 'moderate': 1, 'high': 2}
        stress_encoded = stress_mapping.get(user.stress_level, 1) if user.stress_level else 1
        
        mental_mapping = {'none': 0, 'ptsd': 1, 'depression': 2, 'anxiety': 3, 'bipolar': 4}
        mental_encoded = mental_mapping.get(user.mental_health_condition, 0) if user.mental_health_condition else 0
        
        return {
            'age': user.age or 30,
            'gender': gender_encoded,
            'diet_type': diet_encoded,
            'exercise_level': exercise_encoded,
            'stress_level': stress_encoded,
            'mental_health_condition': mental_encoded,
            'sleep_hours': user.sleep_hours or 7,
            'work_hours_per_week': user.work_hours_per_week or 40,
            'screen_time_per_day': user.screen_time_per_day or 6.0,
            'social_interaction_score': user.self_reported_social_interaction_score or 5,
            'happiness_score': user.happiness_score or 5,
            'engagement': user.engagement_score,
            'motivation': user.motivation_score,
            'segment': user.segment_label if user.segment_label is not None else 4
        }

    def get_segment_name(self, user):
        """Get user segment as string"""
        segment_names = {
            0: "Older High Stress Exhausted",
            1: "Young High Stress Active Social",
            2: "Mid Life Low Stress Depressed",
            3: "Mid Life Thriving Wellness Seeker",
            4: "Working Professional Sedentary Stable"
        }
        segment = segment_names.get(user.segment_label, "Working Professional Sedentary Stable") if user.segment_label is not None else "Working Professional Sedentary Stable"
        return segment

    def adapt_program_with_rl_action(self, base_program, action_id):
        """
        Adapt baseline program based on RL agent's recommended action
        """
        adapted = {k: (v.copy() if isinstance(v, dict) else list(v) if isinstance(v, list) else v) 
                   for k, v in base_program.items()}
        
        action_names = {
            0: "Increase Workout Intensity (IWI)",
            1: "Decrease Workout Intensity (DWI)",
            2: "Increase Meditation Frequency (IMF)",
            3: "Send Motivational Message (SMM)",
            4: "Introduce Journaling Feature (IJF)",
            5: "Maintain Current Plan (MCP)"
        }
        
        # Apply adaptations based on action
        if action_id == 0:  # Increase Workout Intensity
            if "physical_program" in adapted:
                adapted["physical_program"]["intensity"] = "Increased"
                adapted["physical_program"]["progression"] = "Ready for increased challenge"
                adapted["adaptation_reason"] = "RL: Increasing workout intensity based on engagement"
                
        elif action_id == 1:  # Decrease Workout Intensity
            if "physical_program" in adapted:
                adapted["physical_program"]["intensity"] = "Reduced"
                adapted["physical_program"]["progression"] = "Focus on consistency and habit building"
                adapted["adaptation_reason"] = "RL: Reducing intensity to improve adherence"
                
        elif action_id == 2:  # Increase Meditation Frequency
            if "mental_program" in adapted:
                adapted["mental_program"]["frequency"] = "Daily or increased sessions"
                adapted["mental_program"]["focus"] = "Enhanced mindfulness and stress reduction"
                adapted["adaptation_reason"] = "RL: Increasing meditation for better mental health outcomes"
                
        elif action_id == 3:  # Send Motivational Message
            if "reminders" in adapted:
                adapted["reminders"].append("Daily motivational check-in")
                adapted["adaptation_reason"] = "RL: Adding motivational support to boost engagement"
                
        elif action_id == 4:  # Introduce Journaling Feature
            if "mental_program" in adapted:
                if "activities" in adapted["mental_program"]:
                    adapted["mental_program"]["activities"].append("Structured journaling for reflection")
                adapted["adaptation_reason"] = "RL: Adding journaling to improve self-awareness"
                
        else:  # Maintain Current Plan (action_id == 5)
            adapted["adaptation_reason"] = "RL: Current plan working well, maintaining current strategy"
        
        adapted["rl_action"] = action_names.get(action_id, "Unknown")
        return adapted

    def structure_exercises_for_frontend(self, exercises_list, total_duration_str):
        """
        Convert exercise list into structured format with timing for frontend rendering
        """
        structured_exercises = []
        
        # Parse duration string to get minutes (e.g., "30-40 minutes" -> 35)
        duration_minutes = 30  # default
        if total_duration_str:
            numbers = re.findall(r'\d+', total_duration_str)
            if numbers:
                # Take average if range, otherwise take first number
                if len(numbers) >= 2:
                    duration_minutes = (int(numbers[0]) + int(numbers[1])) // 2
                else:
                    duration_minutes = int(numbers[0])
        
        # Calculate time per exercise
        num_exercises = len(exercises_list)
        if num_exercises > 0:
            time_per_exercise = duration_minutes / num_exercises
            
            for i, exercise in enumerate(exercises_list):
                structured_exercises.append({
                    "name": exercise,
                    "order": i + 1,
                    "timing_minutes": round(time_per_exercise, 1),
                    "timing_seconds": round(time_per_exercise * 60, 0)
                })
        
        return structured_exercises

    def structure_activities_for_frontend(self, activities_list, total_duration_str):
        """
        Convert mental activities list into structured format with timing
        """
        return self.structure_exercises_for_frontend(activities_list, total_duration_str)

    @extend_schema(
        summary="Get Personalized Workout Program",
        description="""
        Returns persisted physical + mental programs with nested activities.

        This endpoint is the top-level recommendation call and now mirrors
        `/workout/activity/recommended/` so frontend receives:
        - Program IDs
        - Activity IDs
        - Exact timers (`duration_minutes` and `duration_seconds`)
        - RL action metadata used for training
        """,
        responses={
            200: RecommendedProgramsResponseSerializer,
            401: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Successful Program Response',
                value={
                    "status": "success",
                    "user_segment": "Working Professional Sedentary Stable",
                    "activity_segment": "Moderate Anxiety, Moderate Activity",
                    "rl_action": 3,
                    "rl_action_name": "Send Motivational Message (SMM)",
                    "reason": "Time for a balanced routine combining physical and mental wellness",
                    "physical_program": {
                        "id": 24,
                        "program_type": "physical",
                        "name": "Working Professional Sedentary Stable - Physical Program",
                        "activities": [
                            {
                                "id": 123,
                                "activity_name": "Brisk Walking: 20 Minutes",
                                "duration_minutes": 20,
                                "duration_seconds": 1200,
                                "completed": False
                            }
                        ]
                    },
                    "mental_program": {
                        "id": 25,
                        "program_type": "mental",
                        "name": "Working Professional Sedentary Stable - Mental Program",
                        "activities": [
                            {
                                "id": 124,
                                "activity_name": "Mindfulness Meditation: 10 Minutes",
                                "duration_minutes": 10,
                                "duration_seconds": 600,
                                "completed": False
                            }
                        ]
                    },
                    "total_activities": 2,
                    "user_engagement": 0.65,
                    "user_motivation": 4
                },
                response_only=True
            )
        ]
    )
    def get(self, request):
        """Return persisted recommendation payload with program/activity IDs."""
        return RecommendedActivitiesView().get(request)

    @extend_schema(
        summary="Submit Program Feedback (Legacy)",
        description="""
        **DEPRECATED:** Use `/workout/activity/feedback-batch/` instead for better tracking.
        
        Submit feedback about your wellness program to train the RL agent.
        This endpoint updates your engagement score and trains the recommendation system.
        """,
        request=EngagementFeedbackRequestSerializer,
        responses={
            200: EngagementFeedbackResponseSerializer,
            400: OpenApiTypes.OBJECT,
        },
        deprecated=True
    )
    def post(self, request):
        """
        POST: Accept feedback and trigger RL training
        Updates user engagement metrics and trains RL agent
        """
        user = request.user
        
        # Get feedback from request
        engagement_delta = request.data.get('engagement_delta', 0)  # Change in engagement
        workout_completed = request.data.get('workout_completed', False)
        meditation_completed = request.data.get('meditation_completed', False)
        feedback_rating = request.data.get('feedback_rating', 3)  # 1-5 rating
        
        # Update user metrics
        if workout_completed:
            user.workouts_completed += 1
        if meditation_completed:
            user.meditation_sessions += 1
        
        # Update engagement and motivation scores
        old_engagement = user.engagement_score
        user.engagement_score = max(0, min(1, user.engagement_score + engagement_delta))
        user.motivation_score = max(1, min(5, feedback_rating))
        user.save()
        
        # Get user state for RL
        # Encode categorical fields
        gender_mapping = {'male': 0, 'female': 1, 'other': 2}
        gender_encoded = gender_mapping.get(user.gender, 0) if user.gender else 0
        
        diet_mapping = {'vegetarian': 0, 'vegan': 1, 'balanced': 2, 'junk_food': 3, 'keto': 4}
        diet_encoded = diet_mapping.get(user.diet_type, 2) if user.diet_type else 2
        
        exercise_mapping = {'low': 0, 'moderate': 1, 'high': 2}
        exercise_encoded = exercise_mapping.get(user.exercise_level, 1) if user.exercise_level else 1
        
        stress_mapping = {'low': 0, 'moderate': 1, 'high': 2}
        stress_encoded = stress_mapping.get(user.stress_level, 1) if user.stress_level else 1
        
        mental_mapping = {'none': 0, 'ptsd': 1, 'depression': 2, 'anxiety': 3, 'bipolar': 4}
        mental_encoded = mental_mapping.get(user.mental_health_condition, 0) if user.mental_health_condition else 0
        
        user_state_before = {
            'age': user.age or 30,
            'gender': gender_encoded,
            'diet_type': diet_encoded,
            'exercise_level': exercise_encoded,
            'stress_level': stress_encoded,
            'mental_health_condition': mental_encoded,
            'sleep_hours': user.sleep_hours or 7,
            'work_hours_per_week': user.work_hours_per_week or 40,
            'screen_time_per_day': user.screen_time_per_day or 6.0,
            'social_interaction_score': user.self_reported_social_interaction_score or 5,
            'happiness_score': user.happiness_score or 5,
            'engagement': old_engagement,
            'motivation': feedback_rating,
            'segment': user.segment_label if user.segment_label is not None else 4
        }
        
        user_state_after = {
            'age': user.age or 30,
            'gender': gender_encoded,
            'diet_type': diet_encoded,
            'exercise_level': exercise_encoded,
            'stress_level': stress_encoded,
            'mental_health_condition': mental_encoded,
            'sleep_hours': user.sleep_hours or 7,
            'work_hours_per_week': user.work_hours_per_week or 40,
            'screen_time_per_day': user.screen_time_per_day or 6.0,
            'social_interaction_score': user.self_reported_social_interaction_score or 5,
            'happiness_score': user.happiness_score or 5,
            'engagement': user.engagement_score,
            'motivation': user.motivation_score,
            'segment': user.segment_label if user.segment_label is not None else 4
        }
        
        # Get last recommended action
        last_action = user.last_action_recommended if user.last_action_recommended is not None else 5
        
        # Calculate reward
        reward = RecommendProgram.rl_agent.calculate_reward(user_state_after, last_action)
        
        # Update Q-table with feedback
        RecommendProgram.rl_agent.update_q_value(user_state_before, last_action, reward, user_state_after)
        RecommendProgram.rl_agent.decay_epsilon()
        
        # Save updated agent model
        RecommendProgram.rl_model_manager.save_agent(RecommendProgram.rl_agent)
        
        response_data = {
            "status": "success",
            "message": "Engagement feedback recorded and RL agent updated",
            "engagement_score": user.engagement_score,
            "motivation_score": user.motivation_score,
            "workouts_completed": user.workouts_completed,
            "meditation_sessions": user.meditation_sessions,
            "rl_reward_signal": reward,
            "agent_training_info": {
                "total_episodes_trained": RecommendProgram.rl_agent.training_history['episodes'],
                "current_epsilon": RecommendProgram.rl_agent.epsilon,
                "total_reward": RecommendProgram.rl_agent.training_history['total_reward']
            }
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


@extend_schema(tags=['Workout Programs'])
class EngagementFeedback(APIView):
    """
    Dedicated endpoint for collecting user engagement feedback
    Trains the RL agent to improve future recommendations
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Submit Engagement Feedback",
        description="""
        Submit general engagement feedback to train the RL agent.
        
        **This endpoint:**
        - Records your workout/meditation completion
        - Updates your engagement and motivation scores
        - Trains the RL agent with reward signals
        - Improves future recommendations
        
        **When to use:**
        - After completing workouts or meditation sessions
        - When your engagement level changes
        - To provide feedback on program effectiveness
        
        **Tip:** For detailed activity tracking, use `/workout/activity/feedback-batch/`
        """,
        request=EngagementFeedbackRequestSerializer,
        responses={
            200: EngagementFeedbackResponseSerializer,
            400: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Positive Feedback',
                value={
                    "engagement_delta": 0.15,
                    "workout_completed": True,
                    "meditation_completed": True,
                    "feedback_rating": 5,
                    "notes": "Great session! Felt energized"
                },
                request_only=True
            ),
            OpenApiExample(
                'Negative Feedback',
                value={
                    "engagement_delta": -0.1,
                    "workout_completed": False,
                    "meditation_completed": False,
                    "feedback_rating": 2,
                    "notes": "Too difficult, couldn't complete"
                },
                request_only=True
            )
        ]
    )
    def post(self, request):
        """
        POST engagement feedback data
        
        Expected fields:
        - engagement_delta: float (-1 to 1) - change in engagement
        - workout_completed: bool - whether user completed workout
        - meditation_completed: bool - whether user completed meditation
        - feedback_rating: int (1-5) - user satisfaction rating
        - notes: str (optional) - user feedback notes
        """
        from api.models import CustomUser
        
        user = request.user
        
        # Validate required fields
        if not isinstance(user, CustomUser):
            return Response(
                {"error": "User not found"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extract feedback data
        engagement_delta = request.data.get('engagement_delta', 0)
        workout_completed = request.data.get('workout_completed', False)
        meditation_completed = request.data.get('meditation_completed', False)
        feedback_rating = request.data.get('feedback_rating', 3)
        
        try:
            engagement_delta = float(engagement_delta)
            feedback_rating = int(feedback_rating)
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid data types for engagement_delta or feedback_rating"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Clamp values to valid ranges
        engagement_delta = max(-1, min(1, engagement_delta))
        feedback_rating = max(1, min(5, feedback_rating))
        
        # Store old values
        old_engagement = user.engagement_score
        old_motivation = user.motivation_score
        
        # Update user metrics
        if workout_completed:
            user.workouts_completed += 1
        if meditation_completed:
            user.meditation_sessions += 1
        
        # Update engagement and motivation
        user.engagement_score = max(0, min(1, user.engagement_score + engagement_delta))
        user.motivation_score = feedback_rating
        user.save()
        
        # Prepare states for RL training
        # Encode categorical fields
        gender_mapping = {'male': 0, 'female': 1, 'other': 2}
        gender_encoded = gender_mapping.get(user.gender, 0) if user.gender else 0
        
        diet_mapping = {'vegetarian': 0, 'vegan': 1, 'balanced': 2, 'junk_food': 3, 'keto': 4}
        diet_encoded = diet_mapping.get(user.diet_type, 2) if user.diet_type else 2
        
        exercise_mapping = {'low': 0, 'moderate': 1, 'high': 2}
        exercise_encoded = exercise_mapping.get(user.exercise_level, 1) if user.exercise_level else 1
        
        stress_mapping = {'low': 0, 'moderate': 1, 'high': 2}
        stress_encoded = stress_mapping.get(user.stress_level, 1) if user.stress_level else 1
        
        mental_mapping = {'none': 0, 'ptsd': 1, 'depression': 2, 'anxiety': 3, 'bipolar': 4}
        mental_encoded = mental_mapping.get(user.mental_health_condition, 0) if user.mental_health_condition else 0
        
        segment = user.segment_label if user.segment_label is not None else 4
        
        user_state_before = {
            'age': user.age or 30,
            'gender': gender_encoded,
            'diet_type': diet_encoded,
            'exercise_level': exercise_encoded,
            'stress_level': stress_encoded,
            'mental_health_condition': mental_encoded,
            'sleep_hours': user.sleep_hours or 7,
            'work_hours_per_week': user.work_hours_per_week or 40,
            'screen_time_per_day': user.screen_time_per_day or 6.0,
            'social_interaction_score': user.self_reported_social_interaction_score or 5,
            'happiness_score': user.happiness_score or 5,
            'engagement': old_engagement,
            'motivation': old_motivation,
            'segment': segment
        }
        
        user_state_after = {
            'age': user.age or 30,
            'gender': gender_encoded,
            'diet_type': diet_encoded,
            'exercise_level': exercise_encoded,
            'stress_level': stress_encoded,
            'mental_health_condition': mental_encoded,
            'sleep_hours': user.sleep_hours or 7,
            'work_hours_per_week': user.work_hours_per_week or 40,
            'screen_time_per_day': user.screen_time_per_day or 6.0,
            'social_interaction_score': user.self_reported_social_interaction_score or 5,
            'happiness_score': user.happiness_score or 5,
            'engagement': user.engagement_score,
            'motivation': user.motivation_score,
            'segment': segment
        }
        
        # Get the RL agent and update
        rl_model_manager = RLModelManager(model_dir='api/models')
        rl_agent = rl_model_manager.load_agent()
        
        # Get last recommended action
        last_action = user.last_action_recommended if user.last_action_recommended is not None else 5
        
        # Calculate reward
        reward = rl_agent.calculate_reward(user_state_after, last_action)
        
        # Update Q-table
        rl_agent.update_q_value(user_state_before, last_action, reward, user_state_after)
        rl_agent.decay_epsilon()
        
        # Save updated model
        rl_model_manager.save_agent(rl_agent)
        
        return Response({
            "status": "success",
            "message": "Feedback recorded and RL agent updated",
            "user_metrics": {
                "engagement_score": user.engagement_score,
                "motivation_score": user.motivation_score,
                "workouts_completed": user.workouts_completed,
                "meditation_sessions": user.meditation_sessions
            },
            "training_metrics": {
                "reward_signal": float(reward),
                "action_trained": int(last_action),
                "agent_epsilon": float(rl_agent.epsilon),
                "total_episodes": rl_agent.training_history['episodes']
            }
        }, status=status.HTTP_200_OK)


# New Activity-Based Views with Dynamic Adjustment


@extend_schema(tags=['Activity Recommendations'])
class RecommendedActivitiesView(APIView):
    """
    GET /workout/activity/recommended/
    
    Returns personalized activities based on user's segment and RL agent recommendation.
    Activities are selected based on the RL action and adjusted for difficulty based on recent engagement.
    """
    permission_classes = [IsAuthenticated]
    rl_model_manager = RLModelManager(model_dir='api/models')
    rl_agent = None
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if RecommendedActivitiesView.rl_agent is None:
            RecommendedActivitiesView.rl_agent = RecommendedActivitiesView.rl_model_manager.load_agent()
    
    @extend_schema(
        summary="Get Daily Recommended Activities",
        description="""
        Get personalized activities for today, powered by RL agent.
        
        **How it works:**
        1. System identifies your wellness segment (based on anxiety/activity levels)
        2. RL agent selects optimal action (0-5) based on your engagement history
        3. Activities are chosen and duration/difficulty adjusted dynamically
        4. Two persisted programs are created: one physical and one mental
        5. Timed instruction steps are split into standalone activities when possible
        6. Every activity is saved with an ID and linked to its parent program
        
        **RL Actions:**
        - **0 - Increase Workout Intensity**: More challenging physical activities
        - **1 - Decrease Workout Intensity**: Lighter, easier activities
        - **2 - Increase Meditation**: More mental wellness focus
        - **3 - Motivational Balance**: Mix of physical & mental
        - **4 - Increase Mental Focus**: More reflection and mindfulness activities
        - **5 - Maintain Current**: Keep current difficulty level
        
        **Activity Fields:**
        - `duration_seconds`: Explicit timer value for each activity unit
        - `duration_minutes`: Rounded-up minute equivalent for display compatibility
        - `intensity`: low, moderate, or high
        - `rl_action_id`: Which RL action generated this (0-5)
        - `instructions`: Step-by-step guidance
        - `id`: Persisted ID for completion tracking
        - `program`: Parent program relationship
        
        **Next Steps:**
        1. Complete activities using `/workout/activity/{id}/complete/`
        2. Submit batch feedback using `/workout/activity/feedback-batch/`
        3. RL agent learns and adapts future recommendations
        """,
        responses={
            200: RecommendedProgramsResponseSerializer,
            401: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Success Response',
                value={
                    "status": "success",
                    "user_segment": "Working Professional Sedentary Stable",
                    "activity_segment": "Moderate Anxiety, Moderate Activity",
                    "rl_action": 3,
                    "rl_action_name": "Send Motivational Message (SMM)",
                    "reason": "Time for a balanced routine combining physical and mental wellness",
                    "physical_program": {
                        "id": 24,
                        "program_type": "physical",
                        "name": "Working Professional Sedentary Stable - Physical Program",
                        "activities": [
                            {
                                "id": 123,
                                "activity_name": "Brisk Walking: 20 Minutes",
                                "activity_type": "exercise"
                            }
                        ]
                    },
                    "mental_program": {
                        "id": 25,
                        "program_type": "mental",
                        "name": "Working Professional Sedentary Stable - Mental Program",
                        "activities": [
                            {
                                "id": 124,
                                "activity_name": "Mindfulness Meditation: 10 Minutes",
                                "activity_type": "meditation"
                            }
                        ]
                    },
                    "total_activities": 2,
                    "user_engagement": 0.68,
                    "user_motivation": 4
                },
                response_only=True
            )
        ]
    )
    def get(self, request):
        """Create and return persisted physical + mental programs with activity IDs."""
        user = request.user
        
        try:
            # Get user's segment
            segment = self._get_user_segment(user)
            segment_id = getattr(user, 'segment_label', 4)
            activity_segment = get_activity_segment_key(segment)
            
            # Get RL agent's recommended action
            user_state = self._build_user_state(user, segment_id)
            action = RecommendedActivitiesView.rl_agent.select_action(user_state)
            action_name = RecommendedActivitiesView.rl_agent.get_action_name(action)

            # Keep last action in sync for subsequent RL training endpoints.
            user.last_action_recommended = int(action)
            user.last_recommendation_date = timezone.now()
            user.save(update_fields=['last_action_recommended', 'last_recommendation_date'])
            
            # Get activities using mapped activity segment key
            segment_activities = ACTIVITIES_BY_SEGMENT.get(activity_segment, {})
            physical_activities = segment_activities.get("physical", [])
            all_mental_activities = segment_activities.get("mental", [])
            mental_activities = [
                item for item in all_mental_activities
                if str(item.get("type", "")).lower() != 'journaling'
            ]
            # If a segment has too few meditation items, include journaling templates
            # so we can still build multi-activity sessions.
            if len(mental_activities) < 2 and all_mental_activities:
                mental_activities = list(all_mental_activities)
            
            # Select activities based on RL action
            selected_activities = self._select_activities_by_action(
                action, physical_activities, mental_activities, user, segment
            )
            
            # Get recent engagement data to adjust difficulty
            recent_completions = self._get_recent_engagement(user)
            
            # Adjust selected activities based on engagement
            adjusted_activities = []
            for activity in selected_activities:
                adjusted = RecommendedActivitiesView.rl_agent.adjust_activity_difficulty(
                    activity, recent_completions.get('avg_engagement', 0.5), 
                    recent_completions.get('engagement_history', [])
                )
                adjusted_activities.append(adjusted)

            # Ensure both program groups exist with at least one activity when possible.
            physical_selected = [
                a for a in adjusted_activities
                if self._normalize_activity_type(a.get('type')) == 'exercise'
            ]
            mental_selected = [
                a for a in adjusted_activities
                if self._normalize_activity_type(a.get('type')) == 'meditation'
            ]

            if not physical_selected and physical_activities:
                physical_selected = [random.choice(physical_activities)]
            if not mental_selected and mental_activities:
                mental_selected = [random.choice(mental_activities)]

            physical_program = Program.objects.create(
                user=user,
                program_type=Program.ProgramType.PHYSICAL,
                name="Physical Wellness Program",
                description="Personalized physical wellness activities",
                duration=f"{sum(self._safe_duration_minutes(item.get('duration')) for item in physical_selected)} minutes",
                frequency="Daily",
                intensity=self._pick_dominant_intensity(physical_selected),
                progression="Adjust gradually based on completion and motivation",
                rl_action_id=action,
            )

            mental_program = Program.objects.create(
                user=user,
                program_type=Program.ProgramType.MENTAL,
                name="Mental Wellness Program",
                description="Personalized mental wellness activities",
                duration=f"{sum(self._safe_duration_minutes(item.get('duration')) for item in mental_selected)} minutes",
                frequency="Daily",
                focus="Stress management and emotional regulation",
                rl_action_id=action,
            )

            created_physical = self._create_program_activities(
                user=user,
                program=physical_program,
                segment=segment,
                action=action,
                catalog_activities=physical_selected,
            )
            created_mental = self._create_program_activities(
                user=user,
                program=mental_program,
                segment=segment,
                action=action,
                catalog_activities=mental_selected,
            )

            self._sync_program_duration(physical_program)
            self._sync_program_duration(mental_program)
            
            return Response({
                "status": "success",
                "rl_action": action,
                "rl_action_name": action_name,
                "reason": self._get_action_reason(action),
                "physical_program": ProgramSerializer(physical_program).data,
                "mental_program": ProgramSerializer(mental_program).data,
                "total_activities": len(created_physical) + len(created_mental),
                "user_engagement": recent_completions.get('avg_engagement', 0.5),
                "user_motivation": user.motivation_score if hasattr(user, 'motivation_score') else 3
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_user_segment(self, user):
        """Determine user segment - use stored segment_label from ML model"""
        segment_names = {
            0: "Older High Stress Exhausted",
            1: "Young High Stress Active Social",
            2: "Mid Life Low Stress Depressed",
            3: "Mid Life Thriving Wellness Seeker",
            4: "Working Professional Sedentary Stable"
        }
        
        # Use the segment_label from the ML model prediction
        segment_id = getattr(user, 'segment_label', 4)
        return segment_names.get(segment_id, "Working Professional Sedentary Stable")
    
    def _build_user_state(self, user, segment):
        """Build user state for RL agent"""
        # Encode categorical fields
        gender = getattr(user, 'gender', 'male')
        gender_encoded = 0 if gender == 'male' else 1
        
        diet_mapping = {'vegetarian': 0, 'vegan': 1, 'balanced': 2, 'junk_food': 3, 'keto': 4}
        diet_type = getattr(user, 'diet_type', 'balanced')
        diet_encoded = diet_mapping.get(diet_type, 2)
        
        exercise_mapping = {'low': 0, 'moderate': 1, 'high': 2}
        exercise_level = getattr(user, 'exercise_level', 'moderate')
        exercise_encoded = exercise_mapping.get(exercise_level, 1)
        
        stress_mapping = {'low': 0, 'moderate': 1, 'high': 2}
        stress_level = getattr(user, 'stress_level', 'moderate')
        stress_encoded = stress_mapping.get(stress_level, 1)
        
        mental_mapping = {'none': 0, 'ptsd': 1, 'depression': 2, 'anxiety': 3, 'bipolar': 4}
        mental_health = getattr(user, 'mental_health_condition', 'none')
        mental_encoded = mental_mapping.get(mental_health, 0)
        
        return {
            'age': safe_int_or_default(getattr(user, 'age', None), 30, min_value=0),
            'gender': gender_encoded,
            'diet_type': diet_encoded,
            'exercise_level': exercise_encoded,
            'stress_level': stress_encoded,
            'mental_health_condition': mental_encoded,
            'sleep_hours': safe_float_or_default(getattr(user, 'sleep_hours', None), 7.0, min_value=0.0, max_value=9.0),
            'work_hours_per_week': safe_float_or_default(getattr(user, 'work_hours_per_week', None), 40.0, min_value=0.0, max_value=100.0),
            'screen_time_per_day': safe_float_or_default(getattr(user, 'screen_time_per_day', None), 6.0, min_value=0.0, max_value=24.0),
            'social_interaction_score': safe_int_or_default(getattr(user, 'self_reported_social_interaction_score', None), 5, min_value=0, max_value=10),
            'happiness_score': safe_int_or_default(getattr(user, 'happiness_score', None), 5, min_value=0, max_value=10),
            'engagement': safe_float_or_default(getattr(user, 'engagement_score', None), 0.5, min_value=0.0, max_value=1.0),
            'motivation': safe_int_or_default(getattr(user, 'motivation_score', None), 3, min_value=1, max_value=5),
            # RL state expects an integer segment id, not label text.
            'segment': int(segment) if segment is not None else 4
        }
    
    def _select_activities_by_action(self, action, physical, mental, user, segment):
        """Select a multi-activity session based on RL action with balanced variety."""
        action_targets = {
            # Increase Workout Intensity
            0: {'physical': 3, 'mental': 1},
            # Decrease Workout Intensity
            1: {'physical': 2, 'mental': 1},
            # Increase Meditation Frequency
            2: {'physical': 1, 'mental': 3},
            # Send Motivational Message (balanced)
            3: {'physical': 2, 'mental': 2},
            # Increase Mental Focus
            4: {'physical': 1, 'mental': 3},
            # Maintain Current Plan
            5: {'physical': 2, 'mental': 2},
        }
        targets = action_targets.get(int(action), {'physical': 2, 'mental': 2})

        selected_physical = self._sample_activities(physical, targets['physical'])
        selected_mental = self._sample_activities(mental, targets['mental'])
        selected = list(selected_physical) + list(selected_mental)

        # Top up from whichever pool still has unique items so sessions are not too small.
        desired_total = min(
            targets['physical'] + targets['mental'],
            len(physical) + len(mental),
        )
        if len(selected) < desired_total:
            remaining = [
                item for item in list(physical) + list(mental)
                if item not in selected
            ]
            random.shuffle(remaining)
            selected.extend(remaining[: desired_total - len(selected)])

        return selected

    def _sample_activities(self, catalog, count):
        """Sample up to `count` unique activities from a catalog list."""
        if not catalog or count <= 0:
            return []
        if len(catalog) <= count:
            return list(catalog)
        return random.sample(catalog, count)
    
    def _get_recent_engagement(self, user):
        """Get recent engagement data for the user"""
        recent_activities = Activity.objects.filter(user=user).order_by('-completion_date')[:10]
        
        if recent_activities:
            engagement_scores = [a.engagement_contribution for a in recent_activities if a.engagement_contribution]
            avg_engagement = sum(engagement_scores) / len(engagement_scores) if engagement_scores else 0.5
            return {
                'avg_engagement': avg_engagement,
                'engagement_history': engagement_scores,
                'recent_count': len(recent_activities)
            }
        else:
            return {
                'avg_engagement': 0.5,
                'engagement_history': [],
                'recent_count': 0
            }
    
    def _get_action_reason(self, action):
        """Get human-readable reason for the action"""
        reasons = {
            0: "Your fitness level suggests increasing workout intensity for better results",
            1: "Let's ease up on intensity to prevent burnout",
            2: "Meditation can help with stress management and clarity",
            3: "Time for a balanced routine combining physical and mental wellness",
            4: "Additional mental wellness focus can improve consistency and recovery",
            5: "Your current routine is working well, let's maintain it"
        }
        return reasons.get(action, "Personalized recommendation based on your profile")

    def _safe_duration_minutes(self, value):
        """Convert duration values to a positive integer minute value."""
        try:
            return max(1, int(round(float(value))))
        except (TypeError, ValueError):
            return 10

    def _safe_duration_seconds_from_minutes(self, value):
        """Convert minute-based duration values to positive integer seconds."""
        return self._safe_duration_minutes(value) * 60

    def _duration_parts_to_seconds(self, amount, unit):
        """Convert parsed duration pieces (e.g., 30 + seconds) into seconds."""
        quantity = max(1, int(amount))
        unit_text = str(unit or '').lower()
        if unit_text.startswith('min'):
            return quantity * 60
        return quantity

    def _estimate_repetition_seconds(self, low_reps, high_reps=None):
        """Estimate step duration from repetition counts when no timer is provided."""
        low = max(1, int(low_reps))
        high = max(low, int(high_reps)) if high_reps is not None else low
        average_reps = round((low + high) / 2)
        # Controlled bodyweight tempo: around 4 seconds per repetition.
        return min(180, max(20, average_reps * 4))

    def _compact_whitespace(self, text):
        return re.sub(r'\s+', ' ', str(text or '')).strip()

    def _strip_duration_from_name(self, name):
        """Remove duration markers from activity names (duration stays in dedicated fields)."""
        cleaned = self._compact_whitespace(name)
        if not cleaned:
            return cleaned

        # Examples: "Brisk Walking: 20 Minutes", "Walking - 10 min (Slow Pace)"
        cleaned = re.sub(
            r'\s*[:\-]\s*\d+\s*(?:minutes?|mins?|min)\b',
            '',
            cleaned,
            flags=re.IGNORECASE,
        )
        # Examples: "Child's Pose Breathing (3 min)"
        cleaned = re.sub(
            r'\s*\(\s*\d+\s*(?:minutes?|mins?|min)\s*\)',
            '',
            cleaned,
            flags=re.IGNORECASE,
        )
        # Example fallback: "Brisk Walking 20 Minutes"
        cleaned = re.sub(
            r'\s+\d+\s*(?:minutes?|mins?|min)\b\s*$',
            '',
            cleaned,
            flags=re.IGNORECASE,
        )
        # Examples: "5-Min Gentle Stretching", "10 minute walking"
        cleaned = re.sub(
            r'^\s*\d+\s*[-]?\s*(?:minutes?|mins?|min)\b\s*',
            '',
            cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = self._compact_whitespace(cleaned).strip(':- ')
        return cleaned or self._compact_whitespace(name)

    def _build_step_name(self, parent_name, step_text, prefix=None, round_number=None):
        """Create a short activity name for an extracted step."""
        parent_name = self._strip_duration_from_name(parent_name)
        label = self._compact_whitespace(step_text)
        if '(' in label:
            label = label.split('(', 1)[0].strip()
        label = label.rstrip(':').strip()
        if prefix:
            label = prefix
        if not label:
            label = 'Step'

        name = f"{parent_name} - {label}"
        if round_number is not None:
            name = f"{name} (Round {round_number})"
        return name[:200]

    def _extract_timed_units(self, parent_name, instructions, allow_rep_steps=False):
        """Extract timed or repetition-based instruction lines into standalone units."""
        timed_units = []
        repeat_count = 1

        def append_step(step_name, description, seconds, force_single=False):
            rounds = 1 if force_single else (repeat_count if repeat_count > 1 else 1)
            duration_seconds = max(1, int(seconds))

            for idx in range(rounds):
                round_number = idx + 1 if rounds > 1 else None
                line_description = description
                if round_number is not None:
                    line_description = f"{description} (Round {round_number} of {rounds})"

                timed_units.append({
                    'activity_name': self._build_step_name(parent_name, step_name, round_number=round_number),
                    'description': line_description,
                    'duration_seconds': duration_seconds,
                    'instructions': [line_description],
                })

        timed_step_pattern = re.compile(
            r'^(?:[-*]\s*)?(?:\d+[\.)]\s*)?(?P<value>\d+)\s*'
            r'(?P<unit>seconds?|secs?|minutes?|mins?)\s*:\s*(?P<step>.+)$',
            re.IGNORECASE,
        )
        labeled_duration_pattern = re.compile(
            r'^(?:[-*]\s*)?(?P<label>[A-Za-z][A-Za-z\s\-/]+?)\s*\('
            r'(?P<value>\d+)\s*(?P<unit>seconds?|secs?|minutes?|mins?)\)\s*:\s*(?P<details>.+)$',
            re.IGNORECASE,
        )
        repeat_pattern = re.compile(r'repeat\s+(?P<count>\d+)\s+times', re.IGNORECASE)
        movement_pattern = re.compile(
            r'^(?:[-*]\s*)?(?:\d+[\.)]\s*)?(?P<label>[A-Za-z][A-Za-z0-9\s\'\-/]+?)\s*:\s*(?P<details>.+)$',
            re.IGNORECASE,
        )
        repetition_pattern = re.compile(
            r'(?P<low>\d+)\s*(?:-\s*(?P<high>\d+))?\s*(?:repetitions?|reps?)\b',
            re.IGNORECASE,
        )
        hold_pattern = re.compile(
            r'hold\s+(?:for\s+)?(?P<value>\d+)\s*(?P<unit>seconds?|secs?|minutes?|mins?)\b',
            re.IGNORECASE,
        )
        duration_pattern = re.compile(
            r'(?P<value>\d+)\s*(?P<unit>seconds?|secs?|minutes?|mins?)\b',
            re.IGNORECASE,
        )
        rest_pattern = re.compile(
            r'^(?:[-*]\s*)?(?:\d+[\.)]\s*)?rest(?:\s+for)?\s+(?P<value>\d+)\s*'
            r'(?P<unit>seconds?|secs?|minutes?|mins?)\b(?P<details>.*)$',
            re.IGNORECASE,
        )

        for raw_line in instructions:
            line = self._compact_whitespace(raw_line)
            if not line:
                continue

            repeat_match = repeat_pattern.search(line)
            if repeat_match:
                repeat_count = max(1, int(repeat_match.group('count')))
                continue

            if line.lower().startswith(('tips:', 'safety:', 'benefits:', 'goal:')):
                repeat_count = 1
                continue

            labeled_match = labeled_duration_pattern.match(line)
            if labeled_match:
                label = self._compact_whitespace(labeled_match.group('label')).title()
                details = self._compact_whitespace(labeled_match.group('details'))
                seconds = self._duration_parts_to_seconds(
                    labeled_match.group('value'),
                    labeled_match.group('unit'),
                )
                append_step(label, details or label, seconds, force_single=True)
                repeat_count = 1
                continue

            timed_match = timed_step_pattern.match(line)
            if timed_match:
                seconds = self._duration_parts_to_seconds(
                    timed_match.group('value'),
                    timed_match.group('unit'),
                )
                step = self._compact_whitespace(timed_match.group('step'))
                append_step(step, step, seconds)
                continue

            if allow_rep_steps:
                movement_match = movement_pattern.match(line)
                if movement_match:
                    label = self._compact_whitespace(movement_match.group('label')).rstrip(':')
                    details = self._compact_whitespace(movement_match.group('details'))

                    seconds = None
                    hold_match = hold_pattern.search(details)
                    if hold_match:
                        seconds = self._duration_parts_to_seconds(
                            hold_match.group('value'),
                            hold_match.group('unit'),
                        )

                    if seconds is None:
                        reps_match = repetition_pattern.search(details)
                        if reps_match:
                            seconds = self._estimate_repetition_seconds(
                                reps_match.group('low'),
                                reps_match.group('high'),
                            )

                    if seconds is None and label.lower().startswith('rest'):
                        rest_duration_match = duration_pattern.search(details)
                        if rest_duration_match:
                            seconds = self._duration_parts_to_seconds(
                                rest_duration_match.group('value'),
                                rest_duration_match.group('unit'),
                            )

                    if seconds is not None:
                        append_step(label, f"{label}: {details}", seconds)
                        continue

                rest_match = rest_pattern.match(line)
                if rest_match:
                    rest_text = f"Rest for {rest_match.group('value')} {rest_match.group('unit')}"
                    rest_details = self._compact_whitespace(rest_match.group('details'))
                    if rest_details:
                        rest_text = f"{rest_text} {rest_details}".strip()

                    seconds = self._duration_parts_to_seconds(
                        rest_match.group('value'),
                        rest_match.group('unit'),
                    )
                    append_step('Rest', rest_text, seconds)
                    continue

            line_lower = line.lower()
            if 'cool-down' in line_lower or 'cool down' in line_lower or line_lower.startswith('total:'):
                repeat_count = 1

        return timed_units

    def _expand_catalog_activity(self, item):
        """Split one catalog activity into atomic timer-friendly units when possible."""
        instructions = item.get('instructions', [])
        if not isinstance(instructions, list):
            instructions = [str(instructions)] if instructions else []

        parent_name = self._strip_duration_from_name(item.get('name', 'Unnamed Activity')) or 'Unnamed Activity'
        parent_description = self._compact_whitespace(item.get('description', ''))
        default_seconds = self._safe_duration_seconds_from_minutes(item.get('duration'))
        activity_type = self._normalize_activity_type(item.get('type'))

        timed_units = self._extract_timed_units(
            parent_name,
            instructions,
            allow_rep_steps=activity_type == 'exercise',
        )
        if not timed_units:
            return [{
                'activity_name': parent_name,
                'description': parent_description,
                'duration_seconds': default_seconds,
                'duration_minutes': max(1, (default_seconds + 59) // 60),
                'instructions': instructions,
            }]

        expanded = []
        for unit in timed_units:
            duration_seconds = max(1, int(unit.get('duration_seconds') or default_seconds))
            expanded.append({
                'activity_name': unit.get('activity_name', parent_name)[:200],
                'description': unit.get('description') or parent_description,
                'duration_seconds': duration_seconds,
                'duration_minutes': max(1, (duration_seconds + 59) // 60),
                'instructions': unit.get('instructions') or instructions,
            })

        return expanded

    def _normalize_intensity(self, value):
        intensity = str(value or 'Moderate').strip().lower()
        if intensity.startswith('low'):
            return 'Low'
        if intensity.startswith('high'):
            return 'High'
        return 'Moderate'

    def _normalize_activity_type(self, value):
        """Normalize catalog activity type to Activity model choices."""
        return 'exercise' if str(value).lower() == 'exercise' else 'meditation'

    def _pick_dominant_intensity(self, activities):
        """Return strongest intensity among selected physical activities."""
        rank = {'Low': 1, 'Moderate': 2, 'High': 3}
        dominant = 'Moderate'
        for activity in activities:
            normalized = self._normalize_intensity(activity.get('intensity'))
            if rank[normalized] > rank[dominant]:
                dominant = normalized
        return dominant

    def _sync_program_duration(self, program):
        """Refresh program duration string from persisted child activities."""
        total_seconds = program.activities.aggregate(total=Sum('duration_seconds')).get('total') or 0
        total_minutes = max(1, (int(total_seconds) + 59) // 60) if total_seconds else 0
        duration_label = f"{total_minutes} minutes"

        if program.duration != duration_label:
            program.duration = duration_label
            program.save(update_fields=['duration'])

    def _create_program_activities(self, user, program, segment, action, catalog_activities):
        """Persist selected catalog activities under a program and return created rows."""
        created = []
        now = timezone.now()

        for item in catalog_activities:
            for unit in self._expand_catalog_activity(item):
                created.append(
                    Activity.objects.create(
                        user=user,
                        program=program,
                        activity_name=unit['activity_name'],
                        activity_type=self._normalize_activity_type(item.get('type')),
                        user_segment=segment,
                        rl_action_id=action,
                        description=unit['description'],
                        duration_minutes=unit['duration_minutes'],
                        duration_seconds=unit['duration_seconds'],
                        intensity=self._normalize_intensity(item.get('intensity')),
                        instructions=unit['instructions'],
                        assigned_date=now,
                    )
                )

        return created


@extend_schema(tags=['Workout Programs'])
class ProgramListView(APIView):
    """GET /workout/programs/?type=physical|mental"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List User Programs",
        description="List all persisted programs for the authenticated user. Optionally filter by type.",
        parameters=[
            OpenApiParameter(
                name='type',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                enum=['physical', 'mental'],
                description='Optional program type filter'
            )
        ],
        responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT},
    )
    def get(self, request):
        program_type = request.query_params.get('type')

        programs = Program.objects.filter(user=request.user).prefetch_related('activities')
        if program_type:
            if program_type not in (Program.ProgramType.PHYSICAL, Program.ProgramType.MENTAL):
                return Response(
                    {"status": "error", "message": "Invalid type. Use 'physical' or 'mental'."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            programs = programs.filter(program_type=program_type)

        serialized = ProgramSerializer(programs, many=True)
        return Response(
            {"status": "success", "count": len(serialized.data), "programs": serialized.data},
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=['Workout Programs'])
class ProgramDetailView(APIView):
    """GET /workout/programs/{id}/"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get Program Detail",
        description="Fetch one persisted program with all contained activities.",
        parameters=[
            OpenApiParameter(
                name='program_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Program ID'
            )
        ],
        responses={200: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT},
    )
    def get(self, request, program_id):
        program = Program.objects.filter(user=request.user, id=program_id).prefetch_related('activities').first()
        if not program:
            return Response(
                {"status": "error", "message": "Program not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {"status": "success", "program": ProgramSerializer(program).data},
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=['Activity Tracking'])
class ActivityDetailView(APIView):
    """GET /workout/activity/{activity_id}/"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get Activity Detail",
        description=(
            "Fetch a single activity by ID for the authenticated user, including exact timer "
            "fields (`duration_minutes` and `duration_seconds`)."
        ),
        parameters=[
            OpenApiParameter(
                name='activity_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Activity ID',
            )
        ],
        responses={200: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT},
    )
    def get(self, request, activity_id):
        activity = Activity.objects.filter(user=request.user, id=activity_id).select_related('program').first()
        if not activity:
            return Response(
                {"status": "error", "message": "Activity not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        activity_data = ActivitySerializer(activity).data

        program_status = None
        if activity.program_id:
            program = activity.program
            total = program.activities.count()
            done = program.activities.filter(completed=True).count()
            program_status = {
                'program_id': program.id,
                'completed': program.completed,
                'total_activities': total,
                'completed_activities': done,
                'completion_rate': round(done / total, 2) if total else 0.0,
                'completion_date': program.completion_date.isoformat() if program.completion_date else None,
            }

        return Response(
            {"status": "success", "activity": activity_data, "program_status": program_status},
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=['Activity Tracking'])
class CompleteActivityView(APIView):
    """
    POST /workout/activity/{activity_id}/complete/
    
    Records user's activity completion.
    Calculates engagement contribution for RL training.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Complete an Activity",
        description="""
        Mark an activity as completed.
        
        **What happens:**
        1. Activity is marked as completed with timestamp
        2. Engagement contribution is automatically calculated
        3. Program completion progress is refreshed
        
        **Required Fields:**
        - `completed` (boolean): Whether you completed the activity
        
        **Calculated Metrics:**
        - `engagement_contribution`: 0-1 score used for RL training
        
        **Tip:**
        - Use program or batch feedback endpoints to submit session-level motivation/ratings.
        """,
        parameters=[
            OpenApiParameter(
                name='activity_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='ID of the activity to complete'
            )
        ],
        request=ActivityCompletionRequestSerializer,
        responses={
            200: ActivityCompletionResponseSerializer,
            404: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Completed Activity',
                value={
                    "completed": True
                },
                request_only=True
            )
        ]
    )
    def post(self, request, activity_id):
        """Record activity completion with feedback"""
        user = request.user
        
        try:
            activity = Activity.objects.get(id=activity_id, user=user)
            
            # Update activity with completion data
            activity.completed = request.data.get('completed', False)
            
            if activity.completed:
                activity.completion_date = timezone.now()
            
            # Calculate engagement contribution
            engagement = activity.engagement_contribution
            
            activity.save()

            program_status = None
            if activity.program_id:
                program_status = sync_program_completion(activity.program)
            
            return Response({
                "status": "success",
                "activity_id": activity.id,
                "activity_name": activity.activity_name,
                "duration_minutes": activity.duration_minutes,
                "duration_seconds": activity.duration_seconds,
                "completed": activity.completed,
                "motivation": activity.motivation_after,
                "engagement_contribution": float(engagement),
                "program_status": program_status,
                "user_stats": {
                    "total_activities_completed": user.workouts_completed if hasattr(user, 'workouts_completed') else 0,
                    "engagement_score": float(user.engagement_score) if hasattr(user, 'engagement_score') else 0.5
                }
            }, status=status.HTTP_200_OK)
            
        except Activity.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Activity not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(tags=['Activity Tracking'])
class ActivityFeedbackBatchView(APIView):
    """
    POST /workout/activity/feedback-batch/
    
    Process multiple activity completions, calculate session metrics,
    and train the RL agent with session-level engagement feedback.
    """
    permission_classes = [IsAuthenticated]
    rl_model_manager = RLModelManager(model_dir='api/models')
    rl_agent = None
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if ActivityFeedbackBatchView.rl_agent is None:
            ActivityFeedbackBatchView.rl_agent = ActivityFeedbackBatchView.rl_model_manager.load_agent()
    
    @extend_schema(
        summary="Submit Batch Activity Feedback (RL Training)",
        description="""
        **⭐ PRIMARY ENDPOINT FOR RL TRAINING ⭐**
        
        Submit feedback for multiple completed activities to:
        1. Create a WorkoutSession grouping your activities
        2. Calculate aggregate session metrics
        3. Train the RL agent with comprehensive feedback
        4. Get personalized recommendations for future sessions
        
        **Workflow:**
        ```
        1. Get activities: GET /workout/activity/recommended/
        2. Complete each: POST /workout/activity/{id}/complete/
        3. Submit batch: POST /workout/activity/feedback-batch/ ← YOU ARE HERE
        4. RL agent learns and adapts
        5. Next recommendations are personalized
        ```
        
        **Request Body:**
        - `activities`: Array of activity feedback objects
          - `activity_id`: Activity ID
          - `completed`: true/false
          - `motivation`: 1-5 (motivation level after activity)
        - `overall_session_rating`: 1-5 (how was the overall session?)
        - `notes`: Optional session notes
        
        **What You Get Back:**
        - **Session Info**: Created WorkoutSession with metrics
        - **Aggregate Metrics**: Avg motivation delta, difficulty, enjoyment
        - **RL Training Info**: Reward signal, Q-value update, epsilon
        - **Recommendations**: Suggested modifications for future
        
        **RL Training Details:**
        - `reward_signal`: Calculated from your feedback (higher = better)
        - `action_trained`: Which RL action (0-5) was reinforced
        - `q_value_updated`: Q-table was updated with new knowledge
        - `epsilon_current`: Exploration rate (decreases over time)
        
        **How RL Learns:**
        - High ratings + completion → Increase similar activities
        - Low ratings → Reduce difficulty or change activity type
        - Mixed feedback → Explore alternatives
        - Consistent patterns → Confidence increases, better personalization
        
        **Pro Tips:**
        - Submit batch after each workout session (not individual activities)
        - Be consistent with ratings for better learning
        - The more feedback, the better the recommendations
        - Check `activity_recommendations` for insights
        """,
        request=ActivityFeedbackBatchRequestSerializer,
        responses={
            201: ActivityFeedbackBatchResponseSerializer,
            404: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Successful Session',
                value={
                    "activities": [
                        {
                            "activity_id": 123,
                            "completed": True,
                            "motivation": 5
                        },
                        {
                            "activity_id": 124,
                            "completed": True,
                            "motivation": 5
                        }
                    ],
                    "overall_session_rating": 5,
                    "notes": "Great morning session! Felt energized and ready for the day"
                },
                request_only=True
            ),
            OpenApiExample(
                'Mixed Results',
                value={
                    "activities": [
                        {
                            "activity_id": 125,
                            "completed": True,
                            "motivation": 2
                        },
                        {
                            "activity_id": 126,
                            "completed": False,
                            "motivation": 1
                        }
                    ],
                    "overall_session_rating": 2,
                    "notes": "Too difficult, couldn't finish. Need easier options"
                },
                request_only=True
            )
        ]
    )
    def _process_feedback(self, user, activities_data, overall_rating, session_notes):
        """Persist activity feedback, create session metrics, and train RL once per session."""
        if not activities_data:
            raise ValueError("No activities provided")

        overall_rating = safe_int_or_default(overall_rating, 3, min_value=1, max_value=5)
        session_notes = str(session_notes or "")

        completed_count = 0
        activity_ids = []
        affected_program_ids = set()

        for activity_data in activities_data:
            activity_id = activity_data.get('activity_id')
            activity = Activity.objects.get(id=activity_id, user=user)

            activity.completed = bool(activity_data.get('completed', False))
            activity.motivation_after = safe_int_or_default(
                activity_data.get('motivation', overall_rating),
                overall_rating,
                min_value=1,
                max_value=5,
            )

            if activity.completed:
                activity.completion_date = timezone.now()
                completed_count += 1

            activity.save()
            activity_ids.append(activity.id)
            if activity.program_id:
                affected_program_ids.add(activity.program_id)

        program_updates = []
        for program in Program.objects.filter(user=user, id__in=affected_program_ids):
            summary = sync_program_completion(program)
            if summary:
                program_updates.append(summary)

        session = WorkoutSession.objects.create(
            user=user,
            overall_session_rating=overall_rating,
            session_notes=session_notes,
        )
        session.activities.set(activity_ids)
        session.calculate_metrics()
        session.save()

        session_engagement = session.engagement_contribution

        segment = self._get_user_segment(user)
        segment_id = getattr(user, 'segment_label', 4)

        gender = getattr(user, 'gender', 'male')
        gender_encoded = 0 if gender == 'male' else 1

        diet_mapping = {'vegetarian': 0, 'vegan': 1, 'balanced': 2, 'junk_food': 3, 'keto': 4}
        diet_type = getattr(user, 'diet_type', 'balanced')
        diet_encoded = diet_mapping.get(diet_type, 2)

        stress_mapping = {'low': 0, 'moderate': 1, 'high': 2}
        stress_level = getattr(user, 'stress_level', 'moderate')
        stress_encoded = stress_mapping.get(stress_level, 1)

        mental_mapping = {'none': 0, 'ptsd': 1, 'depression': 2, 'anxiety': 3, 'bipolar': 4}
        mental_health = getattr(user, 'mental_health_condition', 'none')
        mental_encoded = mental_mapping.get(mental_health, 0)

        user_state = {
            'age': safe_int_or_default(getattr(user, 'age', None), 30, min_value=0),
            'gender': gender_encoded,
            'diet_type': diet_encoded,
            'stress_level': stress_encoded,
            'mental_health_condition': mental_encoded,
            'sleep_hours': safe_float_or_default(getattr(user, 'sleep_hours', None), 7.0, min_value=0.0, max_value=9.0),
            'work_hours_per_week': safe_float_or_default(getattr(user, 'work_hours_per_week', None), 40.0, min_value=0.0, max_value=100.0),
            'screen_time_per_day': safe_float_or_default(getattr(user, 'screen_time_per_day', None), 6.0, min_value=0.0, max_value=24.0),
            'social_interaction_score': safe_int_or_default(getattr(user, 'self_reported_social_interaction_score', None), 5, min_value=0, max_value=10),
            'happiness_score': safe_int_or_default(getattr(user, 'happiness_score', None), 5, min_value=0, max_value=10),
            'engagement': safe_float_or_default(session_engagement, 0.5, min_value=0.0, max_value=1.0),
            'motivation': safe_int_or_default(getattr(user, 'motivation_score', None), 3, min_value=1, max_value=5),
            # RL state expects an integer segment id, not label text.
            'segment': int(segment_id) if segment_id is not None else 4
        }

        last_action = safe_int_or_default(getattr(user, 'last_action_recommended', None), 5, min_value=0, max_value=5)

        ActivityFeedbackBatchView.rl_agent.update_q_value(
            user_state, last_action, session.engagement_contribution, user_state
        )
        ActivityFeedbackBatchView.rl_agent.decay_epsilon()

        ActivityFeedbackBatchView.rl_model_manager.save_agent(ActivityFeedbackBatchView.rl_agent)

        activity_segment = get_activity_segment_key(segment)
        next_catalog = ACTIVITIES_BY_SEGMENT.get(activity_segment, {})
        next_mental = [
            item for item in next_catalog.get('mental', [])
            if str(item.get('type', '')).lower() != 'journaling'
        ]
        recommendations = ActivityFeedbackBatchView.rl_agent.recommend_activity_modifications(
            next_catalog.get('physical', []) + next_mental,
            {}  # Would be populated with real engagement history in production
        )

        return {
            "status": "success",
            "session": {
                "session_id": session.id,
                "user": user.username,
                "activities_count": len(activity_ids),
                "completed_activities": completed_count,
                "completion_rate": round(completed_count / max(len(activity_ids), 1), 2),
                "overall_rating": overall_rating,
                "session_engagement_contribution": float(session.engagement_contribution)
            },
            "metrics": {
                "completion_rate": session.completion_rate,
                "avg_motivation": session.avg_motivation_after
            },
            "program_updates": program_updates,
            "rl_training": {
                "action_trained": int(last_action),
                "reward_signal": float(session.engagement_contribution),
                "q_value_updated": True,
                "epsilon_current": float(ActivityFeedbackBatchView.rl_agent.epsilon),
                "total_episodes": ActivityFeedbackBatchView.rl_agent.training_history['episodes'],
                "total_reward": float(ActivityFeedbackBatchView.rl_agent.training_history['total_reward'])
            },
            "activity_recommendations": recommendations
        }

    def post(self, request):
        """Process batch feedback and train RL agent"""
        user = request.user
        
        try:
            activities_data = request.data.get('activities', [])
            overall_rating = request.data.get('overall_session_rating', 3)
            session_notes = request.data.get('notes', '')
            payload = self._process_feedback(user, activities_data, overall_rating, session_notes)
            return Response(payload, status=status.HTTP_201_CREATED)
            
        except ValueError as exc:
            return Response({
                "status": "error",
                "message": str(exc)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Activity.DoesNotExist:
            return Response({
                "status": "error",
                "message": "One or more activities not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_user_segment(self, user):
        """Determine user segment - use stored segment_label from ML model"""
        segment_names = {
            0: "Older High Stress Exhausted",
            1: "Young High Stress Active Social",
            2: "Mid Life Low Stress Depressed",
            3: "Mid Life Thriving Wellness Seeker",
            4: "Working Professional Sedentary Stable"
        }
        
        # Use the segment_label from the ML model prediction
        segment_id = getattr(user, 'segment_label', 4)
        return segment_names.get(segment_id, "Working Professional Sedentary Stable")


@extend_schema(tags=['Activity Tracking'])
class ProgramFeedbackView(ActivityFeedbackBatchView):
    """
    POST /workout/programs/{program_id}/feedback/

    Submit one feedback payload for an entire program and train RL at session level.
    """

    @extend_schema(
        summary="Submit Program Feedback (Single Call RL Training)",
        description="""
        Submit one feedback payload for a whole program without listing each activity ID.

        **What this endpoint does:**
        1. Expands `program_id` into all current activities in that program
        2. Applies `completed` + `motivation` to each activity
        3. Creates a single WorkoutSession
        4. Trains RL once using session-level reward

        This is useful when your client treats the program as one workout session.
        """,
        parameters=[
            OpenApiParameter(
                name='program_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Program ID to submit feedback for',
            )
        ],
        request=ProgramFeedbackRequestSerializer,
        responses={
            201: ActivityFeedbackBatchResponseSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Program Completed',
                value={
                    "completed": True,
                    "motivation": 4,
                    "overall_session_rating": 5,
                    "notes": "Completed the whole program in one session"
                },
                request_only=True
            )
        ]
    )
    def post(self, request, program_id):
        user = request.user

        try:
            program = Program.objects.filter(user=user, id=program_id).prefetch_related('activities').first()
            if not program:
                return Response({
                    "status": "error",
                    "message": "Program not found"
                }, status=status.HTTP_404_NOT_FOUND)

            activities = list(program.activities.all())
            if not activities:
                return Response({
                    "status": "error",
                    "message": "No activities found for this program"
                }, status=status.HTTP_400_BAD_REQUEST)

            overall_rating = request.data.get('overall_session_rating', 3)
            session_notes = request.data.get('notes', '')
            completed = bool(request.data.get('completed', True))
            motivation = safe_int_or_default(
                request.data.get('motivation', overall_rating),
                overall_rating,
                min_value=1,
                max_value=5,
            )

            activities_data = [
                {
                    'activity_id': activity.id,
                    'completed': completed,
                    'motivation': motivation,
                }
                for activity in activities
            ]

            payload = self._process_feedback(user, activities_data, overall_rating, session_notes)
            return Response(payload, status=status.HTTP_201_CREATED)

        except ValueError as exc:
            return Response({
                "status": "error",
                "message": str(exc)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Activity.DoesNotExist:
            return Response({
                "status": "error",
                "message": "One or more activities not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
