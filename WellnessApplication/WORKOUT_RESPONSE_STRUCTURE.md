# Workout Response Structure

## Overview
The workout endpoints now return structured data that makes it easy for the frontend to render timers and exercise lists for physical workout sessions.

## API Endpoints Updated

### 1. GET `/workout/activity/recommended/`
Returns recommended activities in a structured format.

**Response Structure:**
```json
{
  "status": "success",
  "user_segment": "Moderate Anxiety, Moderate Activity",
  "rl_action": 3,
  "rl_action_name": "Send Motivational Message (SMM)",
  "reason": "Personalized recommendation based on your profile",
  "workouts": [
    {
      "workout_name": "Brisk Walking: 20 Minutes",
      "activity_type": "exercise",
      "duration_minutes": 20,
      "intensity": "Moderate",
      "description": "Faster-paced walking that elevates heart rate",
      "exercises": [
        {
          "name": "1. Warm up with 2 minutes of slow walking",
          "order": 1,
          "timing_minutes": 2.9,
          "timing_seconds": 171
        },
        {
          "name": "2. Increase pace to 'brisk' (where talking is possible but requires effort)",
          "order": 2,
          "timing_minutes": 2.9,
          "timing_seconds": 171
        },
        {
          "name": "3. Maintain good posture: shoulders back, core engaged",
          "order": 3,
          "timing_minutes": 2.9,
          "timing_seconds": 171
        }
      ]
    }
  ],
  "total_workouts": 2,
  "user_engagement": 0.68,
  "user_motivation": 4
}
```

### 2. GET `/workout/recommend/`
Returns personalized wellness program with structured exercises.

**Response Structure:**
```json
{
  "user_segment": "Moderate Anxiety, Moderate Activity",
  "recommendation_type": "rl_adapted_program",
  "rl_action": "Maintain Current Plan (MCP)",
  "physical_program": {
    "name": "Walk + Bodyweight Training",
    "description": "Balanced approach combining cardio and strength",
    "exercises": [
      "Brisk walking (20-30 minutes)",
      "Bodyweight exercises (push-ups, squats, planks)",
      "Light resistance movements"
    ],
    "structured_exercises": [
      {
        "name": "Brisk walking (20-30 minutes)",
        "order": 1,
        "timing_minutes": 11.7,
        "timing_seconds": 700
      },
      {
        "name": "Bodyweight exercises (push-ups, squats, planks)",
        "order": 2,
        "timing_minutes": 11.7,
        "timing_seconds": 700
      },
      {
        "name": "Light resistance movements",
        "order": 3,
        "timing_minutes": 11.7,
        "timing_seconds": 700
      }
    ],
    "duration": "30-40 minutes",
    "frequency": "3-4 times per week",
    "intensity": "Moderate"
  },
  "mental_program": {
    "name": "CBT-based Journaling + Mindfulness",
    "description": "Cognitive behavioral techniques with mindfulness",
    "activities": [
      "Daily mood and thought journaling",
      "Weekly structured mindfulness sessions",
      "Gratitude practice"
    ],
    "structured_activities": [
      {
        "name": "Daily mood and thought journaling",
        "order": 1,
        "timing_minutes": 5.8,
        "timing_seconds": 350
      },
      {
        "name": "Weekly structured mindfulness sessions",
        "order": 2,
        "timing_minutes": 5.8,
        "timing_seconds": 350
      },
      {
        "name": "Gratitude practice",
        "order": 3,
        "timing_minutes": 5.8,
        "timing_seconds": 350
      }
    ],
    "duration": "15-20 minutes",
    "frequency": "Daily journaling, 2-3x weekly meditation"
  },
  "engagement_score": 0.65,
  "motivation_score": 4
}
```

## Frontend Usage

### For Timer Implementation
Use the `timing_seconds` field to create countdown timers for each exercise:

```javascript
workouts.forEach(workout => {
  workout.exercises.forEach(exercise => {
    startTimer(exercise.timing_seconds, exercise.name);
  });
});
```

### For Exercise List Rendering
Use the `order` field to display exercises in sequence:

```javascript
<div className="workout">
  <h2>{workout.workout_name}</h2>
  <p>Duration: {workout.duration_minutes} minutes</p>
  <ul className="exercise-list">
    {workout.exercises.map(exercise => (
      <li key={exercise.order}>
        <span className="exercise-name">{exercise.name}</span>
        <span className="exercise-time">{exercise.timing_minutes} min</span>
      </li>
    ))}
  </ul>
</div>
```

### For Progress Tracking
Track completion of individual exercises:

```javascript
const [completedExercises, setCompletedExercises] = useState([]);

const completeExercise = (workoutIndex, exerciseOrder) => {
  setCompletedExercises([...completedExercises, {
    workout: workoutIndex,
    exercise: exerciseOrder,
    completedAt: new Date()
  }]);
};
```

## Key Features

1. **Structured Exercises**: Each workout contains a list of exercises with specific timing
2. **Timing Information**: Both minutes and seconds provided for flexibility
3. **Order Field**: Exercises are numbered for sequential rendering
4. **Duration Metadata**: Total workout duration at the workout level
5. **Backward Compatibility**: Original fields are still present (exercises, activities)

## Benefits for Frontend

- ✅ Easy to implement countdown timers
- ✅ Clear exercise progression
- ✅ Accurate time allocation per exercise
- ✅ Support for workout session tracking
- ✅ Enables real-time progress visualization
