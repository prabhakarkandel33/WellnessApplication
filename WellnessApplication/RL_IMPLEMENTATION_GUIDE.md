# RL Agent Integration - Implementation Guide

## Overview
This implementation integrates a Q-learning Reinforcement Learning agent into your Django Wellness Application to provide adaptive, personalized workout recommendations.

## What Was Created

### 1. **RL Agent Module** (`api/rl_agent.py`)
Contains two main classes:

#### `WellnessRLAgent`
- **Purpose**: Core Q-learning agent for program recommendation optimization
- **Key Methods**:
  - `encode_state(user_state)`: Converts continuous user features to discrete states for Q-table
  - `select_action(state)`: Uses ε-greedy strategy to choose actions
  - `calculate_reward(user_state, action)`: Computes reward: $R = \alpha \cdot E + \beta \cdot M - \lambda \cdot D$
  - `update_q_value()`: Updates Q-table using Q-learning formula
  - `decay_epsilon()`: Gradually reduces exploration rate

- **Action Space** (6 actions):
  - 0: Increase Workout Intensity (IWI)
  - 1: Decrease Workout Intensity (DWI)
  - 2: Increase Meditation Frequency (IMF)
  - 3: Send Motivational Message (SMM)
  - 4: Introduce Journaling Feature (IJF)
  - 5: Maintain Current Plan (MCP)

#### `RLModelManager`
- **Purpose**: Handles persistence of Q-tables and model checkpoints
- Methods:
  - `save_agent()`: Serializes Q-table to JSON
  - `load_agent()`: Restores agent from file or creates new

### 2. **Updated User Model** (`api/models.py`)
Added RL-related fields to `CustomUser`:
- `engagement_score` (0-1): User engagement metric
- `motivation_score` (1-5): User motivation level
- `workouts_completed`: Counter for completed workouts
- `meditation_sessions`: Counter for completed meditations
- `last_action_recommended`: Stores last RL action taken
- `last_recommendation_date`: Timestamp of last recommendation

### 3. **Enhanced Views** (`workout/views.py`)

#### `RecommendProgram` View (Updated)
- **GET**: Returns RL-optimized program recommendation
  - Extracts user state from database
  - Calls `rl_agent.select_action()` to get action
  - Adapts baseline program based on action
  - Saves recommendation metadata to user

- **POST**: Accepts engagement feedback for training
  - Updates user metrics
  - Triggers Q-table update with reward signal
  - Saves updated model to disk

#### `EngagementFeedback` View (New)
- **POST**: Dedicated feedback collection endpoint
- Expected fields:
  ```json
  {
    "engagement_delta": 0.1,      // Change in engagement (-1 to 1)
    "workout_completed": true,     // Did they complete?
    "meditation_completed": false, // Did they complete?
    "feedback_rating": 4           // Satisfaction (1-5)
  }
  ```

### 4. **URL Configuration** (`workout/urls.py`)
- `/recommend/` - GET/POST for program recommendations
- `/feedback/` - POST for engagement feedback

### 5. **Database Migration** (`api/migrations/0003_rl_agent_fields.py`)
Adds new fields to `CustomUser` model

## How It Works

### State Encoding
User attributes are discretized into bins:
- Age: 10-year bins (0-50+)
- BMI: 5-point bins (15-35+)
- Anxiety: 5-point bins (0-20)
- Activity: Days per week (0-7)
- Engagement: 10-point scale (0-1)
- Segment: 6 categories

### Reward Function
$$R(s,a) = 0.5 \cdot E(s') + 0.3 \cdot M(s') - 1.0 \cdot D(s')$$

Where:
- **E(s')**: Engagement score (0-1)
- **M(s')**: Motivation normalized (0-1)
- **D(s')**: Dropout penalty (1 if engagement < 0.1, else 0)

### Q-Learning Update
$$Q(s,a) \leftarrow Q(s,a) + \eta[r + \gamma \max_a Q(s',a') - Q(s,a)]$$

Where:
- η = 0.1 (learning rate)
- γ = 0.9 (discount factor)

### Exploration-Exploitation
Uses ε-greedy strategy:
- Initial ε = 0.3 (30% exploration)
- Decays by 0.995 after each episode
- Minimum ε = 0.05 (5%)

## API Usage Examples

### 1. Get Recommendation
```bash
GET /workout/recommend/
Authorization: Bearer {token}
```

**Response:**
```json
{
  "user_segment": "Wellness Seekers",
  "recommendation_type": "rl_adapted_program",
  "rl_action": "Increase Meditation Frequency (IMF)",
  "physical_program": {...},
  "mental_program": {...},
  "reminders": [...],
  "engagement_score": 0.65,
  "motivation_score": 4
}
```

### 2. Submit Feedback
```bash
POST /workout/feedback/
Authorization: Bearer {token}
Content-Type: application/json

{
  "engagement_delta": 0.1,
  "workout_completed": true,
  "meditation_completed": true,
  "feedback_rating": 5
}
```

**Response:**
```json
{
  "status": "success",
  "user_metrics": {
    "engagement_score": 0.75,
    "motivation_score": 5,
    "workouts_completed": 15,
    "meditation_sessions": 8
  },
  "training_metrics": {
    "reward_signal": 0.35,
    "agent_epsilon": 0.18,
    "total_episodes": 42
  }
}
```

## File Structure
```
api/
├── models.py                    # Updated with engagement fields
├── rl_agent.py                  # RL Agent classes (NEW)
├── migrations/
│   └── 0003_rl_agent_fields.py # Database migration (NEW)

workout/
├── views.py                     # Updated with RL integration
└── urls.py                      # Added feedback endpoint

models/
└── wellness_rl_agent.json       # Saved Q-table (auto-created)
```

## Setup & Deployment

### 1. Create Models Directory
```bash
mkdir -p api/models
```

### 2. Run Migrations
```bash
python manage.py migrate
```

### 3. First Run
The RL agent automatically:
- Creates `api/models/wellness_rl_agent.json` on first request
- Initializes empty Q-table
- Begins learning from user feedback

### 4. Monitor Training
Check agent stats in response:
```json
"training_metrics": {
  "total_episodes": 42,        // Number of updates
  "agent_epsilon": 0.18,       // Current exploration rate
  "total_reward": 8.5          // Sum of all rewards
}
```

## Key Features

✅ **Persistent Learning**: Q-table saved to disk after each update
✅ **Multi-User Support**: Each user generates unique state-action pairs
✅ **Adaptive Actions**: 6 actionable program modifications
✅ **Engagement Tracking**: Metrics tracked per user
✅ **Production Ready**: Handles missing/null values gracefully
✅ **Extensible**: Easy to add new actions or state features

## Future Enhancements

1. **Batch Training**: Periodically retrain on historical user data
2. **Multiple Agents**: Segment-specific agents for better convergence
3. **Neural Networks**: Replace Q-table with Deep Q-Learning
4. **A/B Testing**: Compare old vs new recommendations
5. **Analytics Dashboard**: Track agent performance over time
6. **Offline RL**: Learn from logged interaction data

## Troubleshooting

**Issue**: Model file not found
- **Solution**: Check `api/models/` directory exists and is writable

**Issue**: Q-table not updating
- **Solution**: Verify POST feedback endpoint is receiving data

**Issue**: Poor recommendations early on
- **Solution**: Normal! Agent needs ~50 episodes to learn effectively

## Notes

- The RL agent is **stateless** per request (uses class-level singleton)
- Model is saved **after each feedback** (can be batched if high traffic)
- Missing user fields default to reasonable values (age=30, BMI=25, etc.)
- Segment mapping must match your `SEGMENT_CHOICES` in models.py
