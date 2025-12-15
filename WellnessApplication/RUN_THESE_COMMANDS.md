# 🚀 QUICK START: Exact Commands to Run

## One-Minute Verification

Copy and paste these commands:

```bash
# Navigate to project
cd d:\MajorPrjct\WellnessApplication\WellnessApplication

# Apply migrations
python manage.py migrate

# Run all tests
python manage.py test workout -v 2
```

**Expected result:** `OK (34 tests pass)`

If you see `OK`, skip to the [5-minute testing](#5-minute-testing) section below.

---

## 5-Minute Testing

```bash
# Step 1: Create test user
python manage.py shell

# In the shell, run this:
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.create_user('testuser', 'test@example.com', 'testpass123')
user.age = 35
user.gender = 'M'
user.bmi = 24
user.gad7_score = 12
user.activity_week = 2
user.engagement_score = 0.4
user.motivation_score = 2
user.save()
print("User created!")
exit()

# Step 2: Run tests
python manage.py test workout.tests -v 2
# Should see: OK

# Step 3: Test RL
python manage.py test workout.test_rl_integration -v 2
# Should see: OK

# Step 4: Test API
python manage.py test workout.test_api -v 2
# Should see: OK

# Step 5: All together
python manage.py test workout -v 2
# Should see: OK (34 tests pass)
```

---

## 10-Minute API Testing

### Step 1: Start Server
```bash
python manage.py runserver
```

### Step 2: In Another Terminal Get Token
```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'
```

**Expected output:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAi..."
}
```

Copy the `access` token (the long string)

### Step 3: Test Endpoint 1
```bash
curl -X GET http://localhost:8000/workout/activity/recommended/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
```

**Expected output:**
```json
{
  "status": "success",
  "rl_action": 2,
  "rl_action_name": "Increase Meditation Frequency",
  "recommended_activities": [...]
}
```

### Step 4: Test Endpoint 2
```bash
curl -X POST http://localhost:8000/workout/activity/1/complete/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "completed": true,
    "motivation_before": 2,
    "motivation_after": 4,
    "difficulty_rating": 2,
    "enjoyment_rating": 4
  }'
```

**Expected output:**
```json
{
  "status": "success",
  "completed": true,
  "motivation_delta": 2,
  "engagement_contribution": 0.65
}
```

### Step 5: Test Endpoint 3
```bash
curl -X POST http://localhost:8000/workout/activity/feedback-batch/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "activities": [
      {
        "activity_id": 1,
        "completed": true,
        "motivation_before": 2,
        "motivation_after": 4
      }
    ],
    "overall_session_rating": 4
  }'
```

**Expected output:**
```json
{
  "status": "success",
  "rl_training": {
    "action_trained": 2,
    "reward_signal": 0.65,
    "total_episodes": 1
  }
}
```

### Step 6: Stop Server
Press `Ctrl+C` in the server terminal

---

## Testing All 3 Scenarios

### Scenario 1: Activity Goes Well
```bash
# Motivation before: 2 (low)
# Motivation after: 4 (high)
# Enjoyment: 5 (loved it)

curl -X POST http://localhost:8000/workout/activity/1/complete/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "completed": true,
    "motivation_before": 2,
    "motivation_after": 4,
    "difficulty_rating": 2,
    "enjoyment_rating": 5
  }'

# Expected: engagement_contribution > 0.6 (excellent!)
```

### Scenario 2: Activity Didn't Help
```bash
# Motivation before: 3 (neutral)
# Motivation after: 2 (worse)
# Enjoyment: 2 (disliked)

curl -X POST http://localhost:8000/workout/activity/1/complete/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "completed": true,
    "motivation_before": 3,
    "motivation_after": 2,
    "difficulty_rating": 4,
    "enjoyment_rating": 2
  }'

# Expected: engagement_contribution < 0.3 (poor)
```

### Scenario 3: User Didn't Complete
```bash
# User didn't finish the activity

curl -X POST http://localhost:8000/workout/activity/1/complete/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "completed": false,
    "motivation_before": 3,
    "motivation_after": 3
  }'

# Expected: engagement_contribution < 0 (negative)
```

---

## Django Shell Testing

```bash
python manage.py shell

# Test 1: Create and complete activity
from django.contrib.auth import get_user_model
from workout.models import Activity
from workout.activities import ACTIVITIES_BY_SEGMENT

User = get_user_model()
user = User.objects.get(username='testuser')

# Get specific activity from our definitions
activity_data = ACTIVITIES_BY_SEGMENT['High Anxiety, Low Activity']['physical'][0]

activity = Activity.objects.create(
    user=user,
    activity_name=activity_data['name'],
    activity_type=activity_data['type'],
    duration_minutes=activity_data['duration'],
    intensity=activity_data['intensity'],
    description=activity_data['description'],
    instructions=activity_data['instructions']
)

print(f"Activity created: {activity.activity_name}")
print(f"ID: {activity.id}")

# Complete it
activity.completed = True
activity.motivation_before = 2
activity.motivation_after = 4
activity.difficulty_rating = 2
activity.enjoyment_rating = 4
activity.save()

print(f"Motivation delta: {activity.motivation_delta}")
print(f"Engagement: {activity.engagement_contribution}")

# Test 2: Test RL agent
from api.rl_agent import WellnessRLAgent

agent = WellnessRLAgent()

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

action = agent.select_action(user_state)
print(f"Selected action: {agent.get_action_name(action)}")

next_state = user_state.copy()
next_state['engagement'] = 0.7

agent.update_q_value(user_state, action, reward=0.65, next_state_dict=next_state)
print(f"Q-value updated, Episodes: {agent.training_history['episodes']}")

agent.decay_epsilon()
print(f"Epsilon: {agent.epsilon:.4f}")

# Test 3: Test dynamic adjustment
activity_template = {
    'name': 'Walking: 10 Minutes',
    'type': 'exercise',
    'duration': 10,
    'instructions': ['Walk for 10 minutes']
}

adjusted = agent.adjust_activity_difficulty(
    activity_template,
    engagement_contribution=0.75,
    recent_completions=[0.7, 0.75, 0.8]
)

print(f"Original: {activity_template['duration']} min")
print(f"Adjusted: {adjusted['duration']} min")
print(f"Status: {adjusted['intensity_adjustment']}")

exit()
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'workout'"
```bash
# Make sure you're in the right directory
cd d:\MajorPrjct\WellnessApplication\WellnessApplication

# Try again
python manage.py test workout -v 2
```

### "No such table: workout_activity"
```bash
# Apply migrations
python manage.py migrate

# Then run tests
python manage.py test workout -v 2
```

### "User matching query does not exist"
```bash
# Create the test user first
python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> User.objects.create_user('testuser', 'test@example.com', 'testpass123')
exit()
```

### "Invalid token" in API tests
```bash
# Get a fresh token
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'

# Use the new token in your curl requests
```

---

## Files You Can Check

### After running tests:
```bash
# View results in terminal (already displayed)
# Or check specific test file:
cat workout/tests.py      # See unit tests
cat workout/test_rl_integration.py  # See RL tests
cat workout/test_api.py   # See API tests
```

### After testing APIs:
```bash
# Check database changes:
python manage.py shell
>>> from workout.models import Activity, WorkoutSession
>>> Activity.objects.all()
>>> WorkoutSession.objects.all()
exit()
```

---

## Success Indicators

### ✓ Tests All Pass
```
Ran 34 tests in 1.234s
OK
```

### ✓ Activities Created Successfully
```
Activity created: 5-Min Gentle Stretching
ID: 1
```

### ✓ RL Agent Learning
```
Selected action: Increase Meditation Frequency
Q-value updated, Episodes: 1
Epsilon: 0.2985
```

### ✓ Dynamic Adjustment Working
```
Original: 10 min
Adjusted: 12 min
Status: Increased
```

### ✓ API Endpoints Working
```
status: "success"
rl_action: 2
engagement_contribution: 0.65
```

---

## Complete Test Sequence (Copy & Paste)

```bash
# 1. Navigate
cd d:\MajorPrjct\WellnessApplication\WellnessApplication

# 2. Migrate
python manage.py migrate

# 3. Create user (in shell, then exit)
python manage.py shell
from django.contrib.auth import get_user_model
User = get_user_model()
u = User.objects.create_user('testuser', 'test@example.com', 'testpass123')
u.age=35; u.gender='M'; u.bmi=24; u.gad7_score=12; u.activity_week=2; u.engagement_score=0.4; u.motivation_score=2
u.save()
exit()

# 4. Run all tests
python manage.py test workout -v 2

# If all 34 tests pass, you're done! ✓
```

---

## 🎉 When You See "OK"

That means:
- ✅ All models working
- ✅ All calculations correct
- ✅ RL agent learning
- ✅ All 3 API endpoints working
- ✅ Dynamic difficulty adjustment working
- ✅ Activity removal logic working

Your system is ready!
