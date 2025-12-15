# How to Start & Test: Step-by-Step Instructions

## Prerequisites Check
```bash
# Make sure you're in the right directory
cd d:\MajorPrjct\WellnessApplication\WellnessApplication

# Verify Django is working
python manage.py --version
# Should show: Django 4.x.x
```

---

## STEP 1: Apply Database Migrations (2 minutes)

### What This Does
Creates the Activity and WorkoutSession tables in your database.

### Run This
```bash
python manage.py migrate
```

### Expected Output
```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, sessions, api, workout
Running migrations:
  ...
  Applying workout.0001_activity_models... OK
  ...
```

### Verify Success
```bash
# Check tables were created
python manage.py dbshell
# In the interactive shell:
.tables
# Should see: workout_activity, workout_workoutsession
.quit
```

---

## STEP 2: Create Test Data (2 minutes)

### Create a Test User
```bash
python manage.py shell
```

### Inside the Shell
```python
from django.contrib.auth import get_user_model
from workout.models import Activity

User = get_user_model()

# Create test user
user = User.objects.create_user(
    username='testuser',
    email='test@example.com',
    password='testpass123'
)

# Add profile data needed for segment classification
user.age = 35
user.gender = 'M'
user.bmi = 24
user.gad7_score = 12  # Moderate anxiety
user.activity_week = 2  # Low activity
user.engagement_score = 0.4
user.motivation_score = 2
user.save()

print(f"User created: {user.username}")
print(f"User ID: {user.id}")
exit()
```

---

## STEP 3: Run Unit Tests (2 minutes)

### Test 1: Model Tests
```bash
python manage.py test workout.tests -v 2
```

### Expected Output
```
test_activity_completion_date_set_on_save ... ok
test_activity_creation ... ok
test_activity_engagement_contribution_complete_with_motivation ... ok
test_activity_engagement_contribution_incomplete ... ok
test_activity_is_motivating ... ok
test_activity_is_not_motivating ... ok
test_activity_motivation_delta ... ok
test_session_average_metrics ... ok
test_session_completion_rate ... ok
test_session_completion_rate_partial ... ok
test_session_creation ... ok
test_session_engagement_contribution ... ok
test_activity_decrease_duration_low_engagement ... ok
test_activity_increase_duration_high_engagement ... ok
test_activity_keep_decision_good_engagement ... ok
test_activity_removal_decision_low_engagement ... ok
test_activity_removal_decision_low_engagement ... ok
test_maintain_duration_moderate_engagement ... ok

Ran 18 tests in 0.234s

OK
```

### ✓ If All Pass
Congrats! Models are working correctly.

### ✗ If Any Fail
Check the error message:
```bash
# Example of error
AssertionError: 0.5 != 0.65
# Means: Expected 0.65 but got 0.5
# Check model calculation logic
```

---

## STEP 4: Run RL Integration Tests (2 minutes)

### Test 2: RL Learning Tests
```bash
python manage.py test workout.test_rl_integration -v 2
```

### Expected Output
```
test_action_selection_exploitation ... ok
test_activity_engagement_contributes_to_reward ... ok
test_epsilon_decay ... ok
test_multiple_episodes_q_learning ... ok
test_q_value_update_positive_reward ... ok
test_session_metrics_reflect_activities ... ok

Ran 6 tests in 0.456s

OK
```

### What These Tests Verify
✓ Q-learning algorithm works correctly
✓ Q-values increase with positive rewards
✓ Epsilon (exploration rate) decays over time
✓ Activity feedback flows into RL training
✓ Session metrics aggregate correctly

---

## STEP 5: Run API Tests (3 minutes)

### Test 3: API Endpoint Tests
```bash
python manage.py test workout.test_api -v 2
```

### Expected Output
```
test_batch_feedback_creates_session ... ok
test_batch_feedback_success ... ok
test_batch_feedback_triggers_rl_training ... ok
test_complete_activity_calculates_engagement ... ok
test_complete_activity_calculates_motivation_delta ... ok
test_complete_activity_not_found ... ok
test_complete_activity_success ... ok
test_get_recommended_activities_success ... ok
test_recommended_activities_have_required_fields ... ok
test_recommended_activities_include_adjustment ... ok

Ran 10 tests in 0.567s

OK
```

### What These Tests Verify
✓ GET /workout/activity/recommended/ returns activities
✓ POST /workout/activity/{id}/complete/ records completion
✓ POST /workout/activity/feedback-batch/ trains RL agent
✓ Difficulty adjustments are included
✓ RL training metrics are calculated

---

## STEP 6: Run ALL Tests at Once (5 minutes)

### Complete Test Suite
```bash
python manage.py test workout -v 2
```

### Expected Output
```
...
Ran 34 tests in 1.234s

OK
```

### ✓ Success Checklist
- [x] All model tests pass
- [x] All RL tests pass
- [x] All API tests pass
- [x] No errors or failures
- [x] No skipped tests

---

## STEP 7: Manual Testing with Django Shell (5 minutes)

### Open Shell
```bash
python manage.py shell
```

### Test 1: Create and Complete Activity
```python
from django.contrib.auth import get_user_model
from workout.models import Activity, WorkoutSession
from workout.activities import ACTIVITIES_BY_SEGMENT

User = get_user_model()
user = User.objects.get(username='testuser')

# Get an activity from activities.py
activity_data = ACTIVITIES_BY_SEGMENT['High Anxiety, Low Activity']['physical'][0]

# Create activity
activity = Activity.objects.create(
    user=user,
    activity_name=activity_data['name'],
    activity_type=activity_data['type'],
    duration_minutes=activity_data['duration'],
    intensity=activity_data['intensity'],
    description=activity_data['description'],
    instructions=activity_data['instructions']
)

print(f"Created: {activity.activity_name}")

# Simulate completion
activity.completed = True
activity.motivation_before = 2
activity.motivation_after = 4
activity.difficulty_rating = 2
activity.enjoyment_rating = 4
activity.save()

print(f"Motivation delta: {activity.motivation_delta}")
print(f"Is motivating: {activity.is_motivating}")
print(f"Engagement: {activity.engagement_contribution}")

# Create session
session = WorkoutSession.objects.create(user=user, overall_rating=4)
session.activities.add(activity)
session.calculate_metrics()
session.save()

print(f"Session engagement: {session.engagement_contribution}")
```

### Expected Output
```
Created: 5-Min Gentle Stretching
Motivation delta: 2
Is motivating: True
Engagement: 0.65
Session engagement: 0.65
```

### Test 2: Test RL Agent
```python
from api.rl_agent import WellnessRLAgent

agent = WellnessRLAgent()

# Build user state
user_state = {
    'age': 35,
    'gender': 0,
    'bmi': 24,
    'anxiety_score': 12,
    'activity_week': 2,
    'engagement': 0.4,
    'motivation': 2,
    'segment': 'High Anxiety, Low Activity'
}

# Select action
action = agent.select_action(user_state)
print(f"Selected action: {agent.get_action_name(action)}")

# Train agent
next_state = user_state.copy()
next_state['engagement'] = 0.7

agent.update_q_value(user_state, action, reward=0.65, next_state_dict=next_state)
print(f"Q-value updated")
print(f"Episodes: {agent.training_history['episodes']}")

# Decay epsilon
agent.decay_epsilon()
print(f"Epsilon: {agent.epsilon:.4f}")
```

### Expected Output
```
Selected action: Increase Meditation Frequency (IMF)
Q-value updated
Episodes: 1
Epsilon: 0.2985
```

### Test 3: Test Dynamic Adjustment
```python
from api.rl_agent import WellnessRLAgent

agent = WellnessRLAgent()

activity = {
    'name': 'Walking: 10 Minutes',
    'type': 'exercise',
    'duration': 10,
    'intensity': 'Low',
    'instructions': ['Walk for 10 minutes']
}

# Test with good engagement
adjusted = agent.adjust_activity_difficulty(
    activity,
    engagement_contribution=0.75,
    recent_completions=[0.7, 0.75, 0.8]
)

print(f"Original duration: {activity['duration']} minutes")
print(f"Adjusted duration: {adjusted['duration']} minutes")
print(f"Adjustment: {adjusted['intensity_adjustment']}")
```

### Expected Output
```
Original duration: 10 minutes
Adjusted duration: 12 minutes
Adjustment: Increased
```

### Exit Shell
```python
exit()
```

---

## STEP 8: Manual API Testing (5 minutes)

### Start Development Server
```bash
python manage.py runserver
```

### In Another Terminal: Get Auth Token
```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'
```

### Expected Output
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Copy the access token (long string)

### Test Endpoint 1: Get Recommended Activities
```bash
curl -X GET http://localhost:8000/workout/activity/recommended/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Expected Output
```json
{
  "status": "success",
  "user_segment": "High Anxiety, Low Activity",
  "rl_action": 2,
  "rl_action_name": "Increase Meditation Frequency (IMF)",
  "recommended_activities": [
    {
      "name": "4-7-8 Breathing Technique",
      "type": "meditation",
      "duration": 5,
      "intensity": "Low",
      "intensity_adjustment": "Maintained",
      "reps_adjustment": "Keep current reps",
      "instructions": [...]
    }
  ]
}
```

### Test Endpoint 2: Complete Activity
```bash
# First, create an activity in Django shell and note its ID
# Let's assume ID = 1

curl -X POST http://localhost:8000/workout/activity/1/complete/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "completed": true,
    "motivation_before": 2,
    "motivation_after": 4,
    "difficulty_rating": 2,
    "enjoyment_rating": 4,
    "notes": "Felt good!"
  }'
```

### Expected Output
```json
{
  "status": "success",
  "activity_id": 1,
  "activity_name": "5-Min Gentle Stretching",
  "completed": true,
  "motivation_delta": 2,
  "is_motivating": true,
  "engagement_contribution": 0.65,
  "user_stats": {
    "engagement_score": 0.65
  }
}
```

### Test Endpoint 3: Batch Feedback
```bash
curl -X POST http://localhost:8000/workout/activity/feedback-batch/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "activities": [
      {
        "activity_id": 1,
        "completed": true,
        "motivation_before": 2,
        "motivation_after": 4,
        "difficulty_rating": 2,
        "enjoyment_rating": 4
      }
    ],
    "overall_session_rating": 4,
    "notes": "Great session!"
  }'
```

### Expected Output
```json
{
  "status": "success",
  "session": {
    "session_id": 1,
    "activities_count": 1,
    "completed_activities": 1,
    "completion_rate": 1.0
  },
  "rl_training": {
    "action_trained": 2,
    "reward_signal": 0.65,
    "epsilon_current": 0.2987,
    "total_episodes": 2
  }
}
```

### Stop Server
```bash
# Press Ctrl+C in the server terminal
```

---

## ✅ Complete Testing Checklist

- [ ] Step 1: Migrations applied successfully
- [ ] Step 2: Test user created successfully
- [ ] Step 3: All unit tests pass
- [ ] Step 4: All RL integration tests pass
- [ ] Step 5: All API tests pass
- [ ] Step 6: All tests together pass (34 tests)
- [ ] Step 7: Django shell tests work correctly
- [ ] Step 8: Manual API tests work with curl

---

## 🎯 Summary: What You've Tested

### Models Work ✓
- Activities can be created, completed, and rated
- Engagement contributions calculated correctly
- Sessions aggregate metrics properly

### RL Agent Works ✓
- Q-learning algorithm updates Q-values
- Epsilon decays as expected
- Activities feed into training
- Dynamic difficulty adjustment works
- Activity removal logic works

### APIs Work ✓
- GET /activity/recommended/ returns adapted activities
- POST /activity/{id}/complete/ records feedback
- POST /activity/feedback-batch/ trains RL agent
- All metrics calculated and returned correctly

### Integration Works ✓
- Activities → RL training signal
- User engagement → Q-value updates
- Next user → gets better recommendation

---

## 🚀 You're Ready!

Your system is now fully implemented and tested. The activity-based RL system is working and adapting recommendations based on real user behavior!

**Next:** Create more test data and watch the system learn! 🎉
