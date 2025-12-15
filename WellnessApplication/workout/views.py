from django.shortcuts import render
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
import os
import sys

# Add parent directory to path to import from api
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.rl_agent import WellnessRLAgent, RLModelManager
from workout.serializers import (
    RecommendProgramResponseSerializer,
    EngagementFeedbackRequestSerializer,
    EngagementFeedbackResponseSerializer,
    RecommendedActivitiesResponseSerializer,
    ActivityCompletionRequestSerializer,
    ActivityCompletionResponseSerializer,
    ActivityFeedbackBatchRequestSerializer,
    ActivityFeedbackBatchResponseSerializer
)

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
            "High Anxiety, Low Activity": {
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
            
            "Moderate Anxiety, Moderate Activity": {
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
            
            "Low Anxiety, High Activity": {
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
            
            "Physical Health Risk": {
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
            
            "Wellness Seekers": {
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
            },
            
            "Inactive, Unengaged": {
                "physical_program": {
                    "name": "5-10 Minute Activity Streaks",
                    "description": "Micro-workouts to build exercise habits",
                    "exercises": [
                        "Fun 5-minute walks",
                        "Simple bodyweight movements",
                        "Dance or movement games"
                    ],
                    "duration": "5-10 minutes",
                    "frequency": "Daily micro-sessions",
                    "intensity": "Very low",
                    "progression": "Focus on consistency before increasing duration"
                },
                "mental_program": {
                    "name": "Motivation Boosters & Micro-habits",
                    "description": "Building engagement through small wins",
                    "activities": [
                        "Daily motivational reminders",
                        "Micro-habit challenges",
                        "Achievement celebrations"
                    ],
                    "duration": "2-5 minutes",
                    "frequency": "Multiple daily touchpoints",
                    "focus": "Engagement and motivation building"
                },
                "reminders": [
                    "Gentle activity nudges",
                    "Celebration of small wins",
                    "Motivational check-ins"
                ]
            }
        }

    def get_user_state_dict(self, user):
        """
        Extract user state dictionary from user object for RL agent
        """
        segment_names = {
            0: "High Anxiety, Low Activity",
            1: "Moderate Anxiety, Moderate Activity",
            2: "Low Anxiety, High Activity",
            3: "Physical Health Risk",
            4: "Wellness Seekers",
            5: "Inactive, Unengaged"
        }
        
        segment = segment_names.get(user.segment_label, "Wellness Seekers") if user.segment_label is not None else "Wellness Seekers"
        
        return {
            'age': user.age or 30,
            'gender': 0 if user.gender == 'male' else 1 if user.gender == 'female' else 0,
            'bmi': (user.weight / ((user.height / 100) ** 2)) if user.weight and user.height else 25,
            'anxiety_score': user.gad7_score or 10,
            'activity_week': user.physical_activity_week or 3,
            'engagement': user.engagement_score,
            'motivation': user.motivation_score,
            'segment': segment
        }

    def get_segment_name(self, user):
        """Get user segment as string"""
        segment_names = {
            0: "High Anxiety, Low Activity",
            1: "Moderate Anxiety, Moderate Activity",
            2: "Low Anxiety, High Activity",
            3: "Physical Health Risk",
            4: "Wellness Seekers",
            5: "Inactive, Unengaged"
        }
        segment = segment_names.get(user.segment_label, "Wellness Seekers") if user.segment_label is not None else "Wellness Seekers"
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

    @extend_schema(
        summary="Get Personalized Workout Program",
        description="""
        Returns a complete wellness program tailored to your profile using RL adaptation.
        
        The RL agent analyzes your segment (based on anxiety and activity levels) and 
        selects the optimal program structure, then adapts it based on your engagement history.
        
        **Program Components:**
        - Physical Program: Exercise routines, duration, frequency, intensity
        - Mental Program: Meditation, journaling, mindfulness activities
        - Reminders: Suggested notifications and check-ins
        - RL Adaptation: Dynamic adjustment based on your feedback
        
        **How RL Works:**
        The agent learns from your past engagement to adjust intensity, frequency, 
        and activity types to maximize your wellness outcomes.
        """,
        responses={
            200: RecommendProgramResponseSerializer,
            401: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Successful Program Response',
                value={
                    "user_segment": "Moderate Anxiety, Moderate Activity",
                    "recommendation_type": "rl_adapted_program",
                    "rl_action": "Maintain Current Plan (MCP)",
                    "physical_program": {
                        "name": "Walk + Bodyweight Training",
                        "description": "Balanced approach combining cardio and strength",
                        "exercises": ["Brisk walking", "Push-ups", "Squats"],
                        "duration": "30-40 minutes",
                        "frequency": "3-4 times per week",
                        "intensity": "Moderate"
                    },
                    "mental_program": {
                        "name": "CBT-based Journaling + Mindfulness",
                        "activities": ["Daily journaling", "Meditation"],
                        "duration": "15-20 minutes",
                        "frequency": "Daily"
                    },
                    "engagement_score": 0.65,
                    "motivation_score": 4
                },
                response_only=True
            )
        ]
    )
    def get(self, request):
        """
        GET: Return baseline program with RL-based adaptations
        """
        user = request.user
        
        # Get user segment
        user_segment = self.get_segment_name(user)
        
        # Get user state for RL agent
        user_state = self.get_user_state_dict(user)
        
        # Use RL agent to select action
        action_id = RecommendProgram.rl_agent.select_action(user_state)
        
        # Get baseline program
        if user_segment in self.program_recommendations:
            program_data = self.program_recommendations[user_segment]
        else:
            program_data = self.program_recommendations["Wellness Seekers"]
            user_segment = "Wellness Seekers"
        
        # Adapt program based on RL action
        adapted_program = self.adapt_program_with_rl_action(program_data, action_id)
        
        # Save recommendation metadata to user
        user.last_action_recommended = action_id
        user.last_recommendation_date = timezone.now()
        user.save(update_fields=['last_action_recommended', 'last_recommendation_date'])
        
        recommended_program = {
            "user_segment": user_segment,
            "recommendation_type": "rl_adapted_program",
            "rl_action": RecommendProgram.rl_agent.get_action_name(action_id),
            "physical_program": adapted_program.get("physical_program", {}),
            "mental_program": adapted_program.get("mental_program", {}),
            "reminders": adapted_program.get("reminders", []),
            "adaptation_reason": adapted_program.get("adaptation_reason", ""),
            "engagement_score": user.engagement_score,
            "motivation_score": user.motivation_score,
            "personalization_note": "This program is personalized using AI-driven reinforcement learning based on your profile and past engagement.",
            "next_steps": [
                "Follow the recommended program for optimal results",
                "Track your engagement to enable further personalization",
                "Provide feedback on program suitability"
            ]
        }
        
        return Response(recommended_program, status=status.HTTP_200_OK)

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
        user_state_before = {
            'age': user.age or 30,
            'gender': 0 if user.gender == 'male' else 1,
            'bmi': (user.weight / ((user.height / 100) ** 2)) if user.weight and user.height else 25,
            'anxiety_score': user.gad7_score or 10,
            'activity_week': user.physical_activity_week or 3,
            'engagement': old_engagement,
            'motivation': feedback_rating,
            'segment': self.get_segment_name(user)
        }
        
        user_state_after = {
            'age': user.age or 30,
            'gender': 0 if user.gender == 'male' else 1,
            'bmi': (user.weight / ((user.height / 100) ** 2)) if user.weight and user.height else 25,
            'anxiety_score': user.gad7_score or 10,
            'activity_week': user.physical_activity_week or 3,
            'engagement': user.engagement_score,
            'motivation': user.motivation_score,
            'segment': self.get_segment_name(user)
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
        segment_names = {
            0: "High Anxiety, Low Activity",
            1: "Moderate Anxiety, Moderate Activity",
            2: "Low Anxiety, High Activity",
            3: "Physical Health Risk",
            4: "Wellness Seekers",
            5: "Inactive, Unengaged"
        }
        segment = segment_names.get(user.segment_label, "Wellness Seekers") if user.segment_label else "Wellness Seekers"
        
        user_state_before = {
            'age': user.age or 30,
            'gender': 0 if user.gender == 'male' else 1,
            'bmi': (user.weight / ((user.height / 100) ** 2)) if user.weight and user.height else 25,
            'anxiety_score': user.gad7_score or 10,
            'activity_week': user.physical_activity_week or 3,
            'engagement': old_engagement,
            'motivation': old_motivation,
            'segment': segment
        }
        
        user_state_after = {
            'age': user.age or 30,
            'gender': 0 if user.gender == 'male' else 1,
            'bmi': (user.weight / ((user.height / 100) ** 2)) if user.weight and user.height else 25,
            'anxiety_score': user.gad7_score or 10,
            'activity_week': user.physical_activity_week or 3,
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

from workout.models import Activity, WorkoutSession
from workout.activities import ACTIVITIES_BY_SEGMENT
from django.db.models import Avg, Sum, Count
import random


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
        Get 3-5 personalized activities for today, powered by RL agent.
        
        **How it works:**
        1. System identifies your wellness segment (based on anxiety/activity levels)
        2. RL agent selects optimal action (0-5) based on your engagement history
        3. Activities are chosen and duration/difficulty adjusted dynamically
        4. You receive a mix of physical and mental wellness activities
        
        **RL Actions:**
        - **0 - Increase Workout Intensity**: More challenging physical activities
        - **1 - Decrease Workout Intensity**: Lighter, easier activities
        - **2 - Increase Meditation**: More mental wellness focus
        - **3 - Motivational Balance**: Mix of physical & mental
        - **4 - Introduce Journaling**: Focus on reflection activities
        - **5 - Maintain Current**: Keep current difficulty level
        
        **Activity Fields:**
        - `duration_minutes`: Dynamically adjusted (10-60 min)
        - `intensity`: low, moderate, or high
        - `rl_action_id`: Which RL action generated this (0-5)
        - `instructions`: Step-by-step guidance
        
        **Next Steps:**
        1. Complete activities using `/workout/activity/{id}/complete/`
        2. Submit batch feedback using `/workout/activity/feedback-batch/`
        3. RL agent learns and adapts future recommendations
        """,
        responses={
            200: RecommendedActivitiesResponseSerializer,
            401: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Success Response',
                value={
                    "status": "success",
                    "user_segment": "Moderate Anxiety, Moderate Activity",
                    "rl_action": 3,
                    "rl_action_name": "Send Motivational Message (SMM)",
                    "reason": "Time for a balanced routine combining physical and mental wellness",
                    "recommended_activities": [
                        {
                            "id": 123,
                            "activity_name": "Morning Yoga Flow",
                            "activity_type": "physical",
                            "duration_minutes": 25,
                            "intensity": "moderate",
                            "instructions": "1. Start with breathing...",
                            "user_segment": "Moderate Anxiety, Moderate Activity",
                            "rl_action_id": 3,
                            "assigned_date": "2025-12-15",
                            "completed": False
                        },
                        {
                            "id": 124,
                            "activity_name": "Mindful Breathing",
                            "activity_type": "mental",
                            "duration_minutes": 15,
                            "intensity": "low",
                            "rl_action_id": 3
                        }
                    ],
                    "total_activities": 2,
                    "user_engagement": 0.68,
                    "user_motivation": 4
                },
                response_only=True
            )
        ]
    )
    def get(self, request):
        """Get recommended activities for the user"""
        user = request.user
        
        try:
            # Get user's segment
            segment = self._get_user_segment(user)
            
            # Get RL agent's recommended action
            user_state = self._build_user_state(user, segment)
            action = RecommendedActivitiesView.rl_agent.select_action(user_state)
            action_name = RecommendedActivitiesView.rl_agent.get_action_name(action)
            
            # Get activities for this segment
            segment_activities = ACTIVITIES_BY_SEGMENT.get(segment, {})
            physical_activities = segment_activities.get("physical", [])
            mental_activities = segment_activities.get("mental", [])
            
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
            
            return Response({
                "status": "success",
                "user_segment": segment,
                "rl_action": action,
                "rl_action_name": action_name,
                "reason": self._get_action_reason(action),
                "recommended_activities": adjusted_activities,
                "total_activities": len(adjusted_activities),
                "user_engagement": recent_completions.get('avg_engagement', 0.5),
                "user_motivation": user.motivation_score if hasattr(user, 'motivation_score') else 3
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_user_segment(self, user):
        """Determine user segment based on anxiety and activity levels"""
        anxiety_score = getattr(user, 'gad7_score', 10)
        activity_week = getattr(user, 'activity_week', 3)
        
        if anxiety_score > 15 and activity_week < 3:
            return "High Anxiety, Low Activity"
        elif anxiety_score > 10 and activity_week < 4:
            return "Moderate Anxiety, Moderate Activity"
        elif anxiety_score < 10 and activity_week >= 4:
            return "Low Anxiety, High Activity"
        else:
            return "Physical Health Risk"
    
    def _build_user_state(self, user, segment):
        """Build user state for RL agent"""
        return {
            'age': getattr(user, 'age', 30),
            'gender': 1 if getattr(user, 'gender', 'M') == 'F' else 0,
            'bmi': getattr(user, 'bmi', 25),
            'anxiety_score': getattr(user, 'gad7_score', 10),
            'activity_week': getattr(user, 'activity_week', 3),
            'engagement': getattr(user, 'engagement_score', 0.5),
            'motivation': getattr(user, 'motivation_score', 3),
            'segment': segment
        }
    
    def _select_activities_by_action(self, action, physical, mental, user, segment):
        """Select activities based on RL action"""
        activities = []
        
        # Action-based selection
        if action == 0:  # Increase Workout Intensity
            activities.extend(random.sample(physical, min(2, len(physical))))
        elif action == 1:  # Decrease Workout Intensity
            activities.extend(random.sample(physical, min(1, len(physical))))
        elif action == 2:  # Increase Meditation Frequency
            activities.extend(random.sample(mental, min(2, len(mental))))
        elif action == 3:  # Send Motivational Message
            activities.extend(random.sample(physical, min(1, len(physical))))
            activities.extend(random.sample(mental, min(1, len(mental))))
        elif action == 4:  # Introduce Journaling Feature
            activities.extend(random.sample(mental, min(2, len(mental))))
        else:  # Maintain Current Plan (action 5)
            activities.extend(random.sample(physical, min(1, len(physical))))
            activities.extend(random.sample(mental, min(1, len(mental))))
        
        return activities
    
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
            4: "Journaling can help process emotions and track progress",
            5: "Your current routine is working well, let's maintain it"
        }
        return reasons.get(action, "Personalized recommendation based on your profile")


@extend_schema(tags=['Activity Tracking'])
class CompleteActivityView(APIView):
    """
    POST /workout/activity/{activity_id}/complete/
    
    Records user's activity completion with motivation feedback.
    Calculates engagement contribution for RL training.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Complete an Activity",
        description="""
        Mark an activity as completed and provide motivation feedback.
        
        **What happens:**
        1. Activity is marked as completed with timestamp
        2. Your motivation level is recorded
        3. Engagement contribution is automatically calculated
        4. Your user engagement score is updated
        
        **Required Fields:**
        - `completed` (boolean): Whether you completed the activity
        - `motivation` (1-5): Your motivation level after the activity
        
        **Calculated Metrics:**
        - `engagement_contribution`: 0-1 score used for RL training
        
        **Tips:**
        - Higher motivation (4-5) signals the activity worked well for you
        - Lower motivation (1-2) tells the RL agent to adjust future recommendations
        - Be consistent with your ratings for better personalization
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
                'High Motivation',
                value={
                    "completed": True,
                    "motivation": 5
                },
                request_only=True
            ),
            OpenApiExample(
                'Low Motivation',
                value={
                    "completed": True,
                    "motivation": 2
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
            activity.motivation_after = request.data.get('motivation', 3)
            
            if activity.completed:
                activity.completion_date = timezone.now()
            
            # Calculate engagement contribution
            engagement = activity.engagement_contribution
            
            activity.save()
            
            return Response({
                "status": "success",
                "activity_id": activity.id,
                "activity_name": activity.activity_name,
                "completed": activity.completed,
                "motivation": activity.motivation_after,
                "engagement_contribution": float(engagement),
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
    def post(self, request):
        """Process batch feedback and train RL agent"""
        user = request.user
        
        try:
            activities_data = request.data.get('activities', [])
            overall_rating = request.data.get('overall_session_rating', 3)
            session_notes = request.data.get('notes', '')
            
            # Update individual activities
            completed_count = 0
            total_engagement = 0
            activity_ids = []
            
            for activity_data in activities_data:
                activity_id = activity_data.get('activity_id')
                activity = Activity.objects.get(id=activity_id, user=user)
                
                activity.completed = activity_data.get('completed', False)
                activity.motivation_after = activity_data.get('motivation', 3)
                
                if activity.completed:
                    activity.completion_date = timezone.now()
                    completed_count += 1
                
                activity.save()
                activity_ids.append(activity.id)
                total_engagement += activity.engagement_contribution
            
            # Create or update workout session
            session = WorkoutSession.objects.create(user=user, overall_rating=overall_rating, notes=session_notes)
            session.activities.set(activity_ids)
            session.calculate_metrics()
            session.save()
            
            # Get engagement contribution for RL training
            session_engagement = session.engagement_contribution
            
            # Train RL agent with session-level feedback
            segment = self._get_user_segment(user)
            user_state = {
                'age': getattr(user, 'age', 30),
                'gender': 1 if getattr(user, 'gender', 'F') == 'F' else 0,
                'bmi': getattr(user, 'bmi', 25),
                'anxiety_score': getattr(user, 'gad7_score', 10),
                'activity_week': getattr(user, 'activity_week', 3),
                'engagement': float(session_engagement),
                'motivation': getattr(user, 'motivation_score', 3),
                'segment': segment
            }
            
            # Get last recommended action (from request or user's last action)
            last_action = getattr(user, 'last_action_recommended', 5)
            
            # Update RL agent with training signal
            activity_feedback_state = {
                'engagement': float(session_engagement),
                'motivation': overall_rating
            }
            
            ActivityFeedbackBatchView.rl_agent.update_q_value(
                user_state, last_action, session.engagement_contribution, user_state
            )
            ActivityFeedbackBatchView.rl_agent.decay_epsilon()
            
            # Save updated agent
            ActivityFeedbackBatchView.rl_model_manager.save_agent(ActivityFeedbackBatchView.rl_agent)
            
            # Get activity recommendations for next session
            recommendations = ActivityFeedbackBatchView.rl_agent.recommend_activity_modifications(
                ACTIVITIES_BY_SEGMENT.get(segment, {}).get('physical', []) + 
                ACTIVITIES_BY_SEGMENT.get(segment, {}).get('mental', []),
                {}  # Would be populated with real engagement history in production
            )
            
            return Response({
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
                "rl_training": {
                    "action_trained": int(last_action),
                    "reward_signal": float(session.engagement_contribution),
                    "q_value_updated": True,
                    "epsilon_current": float(ActivityFeedbackBatchView.rl_agent.epsilon),
                    "total_episodes": ActivityFeedbackBatchView.rl_agent.training_history['episodes'],
                    "total_reward": float(ActivityFeedbackBatchView.rl_agent.training_history['total_reward'])
                },
                "activity_recommendations": recommendations
            }, status=status.HTTP_201_CREATED)
            
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
        """Determine user segment based on anxiety and activity levels"""
        anxiety_score = getattr(user, 'gad7_score', 10)
        activity_week = getattr(user, 'activity_week', 3)
        
        if anxiety_score > 15 and activity_week < 3:
            return "High Anxiety, Low Activity"
        elif anxiety_score > 10 and activity_week < 4:
            return "Moderate Anxiety, Moderate Activity"
        elif anxiety_score < 10 and activity_week >= 4:
            return "Low Anxiety, High Activity"
        else:
            return "Physical Health Risk"
