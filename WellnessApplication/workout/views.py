from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

class RecommendProgram(APIView):
    """
    View to recommend a workout program based on user profile.
    Implements the baseline program recommendations from Table 4.1 in the project report.
    """
    permission_classes = [IsAuthenticated]

    def __init__(self):
        super().__init__()
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

    def get(self, request):
        user = request.user
        
        # Get user segment - fallback to a default if not set
        try:
            user_segment = user.segment_label
        except AttributeError:
            # Default segment if user hasn't been classified yet
            user_segment = "Wellness Seekers"
        
        # Handle case where segment_label might be None or empty
        if not user_segment or user_segment == "xxxx":
            user_segment = "Wellness Seekers"
        
        # Get the program recommendation for this segment
        if user_segment in self.program_recommendations:
            program_data = self.program_recommendations[user_segment]
            
            recommended_program = {
                "user_segment": user_segment,
                "recommendation_type": "baseline_program",
                "physical_program": program_data["physical_program"],
                "mental_program": program_data["mental_program"],
                "reminders": program_data["reminders"],
                "personalization_note": "This is your baseline program. It will be adapted based on your engagement and progress.",
                "next_steps": [
                    "Complete the initial assessment if you haven't already",
                    "Start with the recommended frequency and adjust as needed",
                    "Track your engagement to enable personalized adaptations"
                ]
            }
        else:
            # Fallback for unknown segments
            recommended_program = {
                "user_segment": user_segment,
                "error": "Segment not recognized",
                "fallback_program": self.program_recommendations["Wellness Seekers"],
                "message": "Using general wellness program as fallback. Please complete profile assessment for personalized recommendations."
            }
        
        return Response(recommended_program, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Alternative endpoint to get recommendations with additional user data
        """
        user = request.user
        
        # Get segment from request data or user profile
        user_segment = request.data.get('segment_label') or getattr(user, 'segment_label', 'Wellness Seekers')
        
        # Additional parameters for future RL adaptation
        current_engagement = request.data.get('engagement_score', 0.5)
        weeks_active = request.data.get('weeks_active', 0)
        
        if user_segment in self.program_recommendations:
            program_data = self.program_recommendations[user_segment]
            
            # Basic adaptation logic (this will be replaced by RL in future)
            adapted_program = self._adapt_program_basic(program_data, current_engagement, weeks_active)
            
            recommended_program = {
                "user_segment": user_segment,
                "recommendation_type": "adapted_program",
                "current_engagement": current_engagement,
                "weeks_active": weeks_active,
                "adapted_program": adapted_program,
                "adaptation_note": "Program adapted based on your current engagement level and activity history."
            }
        else:
            recommended_program = {
                "error": "Invalid segment provided",
                "available_segments": list(self.program_recommendations.keys())
            }
        
        return Response(recommended_program, status=status.HTTP_200_OK)
    
    def _adapt_program_basic(self, base_program, engagement, weeks_active):
        """
        Basic program adaptation logic (placeholder for RL integration)
        """
        adapted = base_program.copy()
        
        # Simple rule-based adaptation
        if engagement < 0.3:  # Low engagement
            # Reduce intensity and frequency
            adapted["physical_program"]["frequency"] = "2 times per week"
            adapted["physical_program"]["duration"] = "15-20 minutes"
            adapted["adaptation_reason"] = "Reduced intensity due to low engagement"
            
        elif engagement > 0.8 and weeks_active > 4:  # High engagement, experienced user
            # Slightly increase challenge
            adapted["physical_program"]["progression"] = "Ready for increased intensity"
            adapted["adaptation_reason"] = "Increased challenge due to high engagement and experience"
        
        return adapted