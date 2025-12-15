# Quick Start: Testing the Activity-RL System

## 5 Minutes: Run All Tests

```bash
# 1. Apply migrations
python manage.py migrate

# 2. Run all tests
python manage.py test workout -v 2

# 3. Check results
# Should see: OK (passed all tests)
```

---

## Testing Flow

### Step 1: Database Setup (1 min)
```bash
python manage.py migrate
```

### Step 2: Unit Tests (2 min)
```bash
python manage.py test workout.tests -v 2
```
Tests:
- ✓ Activity model creation
- ✓ Motivation calculations
- ✓ Engagement contribution
- ✓ WorkoutSession metrics

### Step 3: RL Integration Tests (2 min)
```bash
python manage.py test workout.test_rl_integration -v 2
```
Tests:
- ✓ Q-value updates with positive rewards
- ✓ Epsilon decay over episodes
- ✓ Activity engagement feeds RL training
- ✓ Session metrics aggregate correctly

### Step 4: API Tests (3 min)
```bash
python manage.py test workout.test_api -v 2
```
Tests:
- ✓ GET /activity/recommended/ returns activities
- ✓ POST /activity/{id}/complete/ records completion
- ✓ POST /activity/feedback-batch/ trains RL agent
- ✓ RL agent receives training signal

### Step 5: Manual Testing (5 min)
```bash
# Start server
python manage.py runserver

# In another terminal, run curl commands
# See ACTIVITY_TESTING_GUIDE.md Part 5 for examples
```

---

## Key Testing Scenarios

### Scenario 1: User Completes Activity with Motivation Boost
```python
# Activity: "4-7-8 Breathing Technique"
# Motivation before: 2/5 (anxious)
# Motivation after: 5/5 (calm)
# Enjoyment: 5/5 (loved it)

# Expected:
# - motivation_delta = 3 (huge improvement)
# - is_motivating = True
# - engagement_contribution = 0.8+ (excellent!)
# - RL agent learns: This action is GOOD for this user type
```

### Scenario 2: User Struggles with Activity
```python
# Activity: "HIIT Workout: 20 Minutes"
# Motivation before: 4/5
# Motivation after: 1/5 (burned out)
# Enjoyment: 1/5 (hated it)

# Expected:
# - motivation_delta = -3 (worse!)
# - is_motivating = False
# - engagement_contribution = 0.1 (poor)
# - RL agent learns: Don't recommend this action
```

### Scenario 3: RL Agent Adapts Activity Difficulty
```python
# User has high engagement (0.75+) on last 5 sessions

# Expected:
# - Activity duration increases by 15%
# - Reps increase by 2-3 per set
# - intensity_adjustment = "Increased"

# User has low engagement (0.2-) on last 5 sessions

# Expected:
# - Activity duration decreases by 15%
# - Reps decrease by 2-3 per set
# - intensity_adjustment = "Decreased"
```

---

## What to Look For in Test Output

### ✓ Good Signs (Tests Passing)
```
Ran 30 tests in 2.345s
OK
```

### ✗ Bad Signs (Tests Failing)
```
Ran 30 tests in 2.345s
FAILED (failures=1, errors=1)
AssertionError: 0.5 != 0.65
```

### ✓ Good API Response
```json
{
  "status": "success",
  "recommended_activities": [
    {
      "name": "Meditation",
      "duration": 10,
      "intensity_adjustment": "Maintained"
    }
  ],
  "rl_training": {
    "episodes": 15,
    "epsilon_current": 0.245
  }
}
```

---

## Testing Checklist

Before you're done, verify:

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] All API tests pass
- [ ] Migration created successfully
- [ ] Can create activities in shell
- [ ] Activities calculate engagement correctly
- [ ] RL agent Q-table updates
- [ ] Epsilon decays properly
- [ ] GET /activity/recommended/ works
- [ ] POST /activity/{id}/complete/ works
- [ ] POST /activity/feedback-batch/ works
- [ ] RL agent receives training signal

---

## File Locations

```
workout/
├── tests.py                          # Unit tests
├── test_rl_integration.py           # RL integration tests
├── test_api.py                      # API tests
├── models.py                        # Activity, WorkoutSession
├── activities.py                    # Concrete activities
├── views.py                         # API views
├── urls.py                          # URL routes
└── migrations/
    └── 0001_activity_models.py      # Database migration

ACTIVITY_TESTING_GUIDE.md             # Full testing guide
ACTIVITY_RL_SUMMARY.md                # System overview
```

---

## Debugging Tips

### Check RL Agent State
```bash
python manage.py shell
>>> from api.rl_agent import WellnessRLAgent
>>> agent = WellnessRLAgent()
>>> print(f"Q-table entries: {len(agent.q_table)}")
>>> print(f"Epsilon: {agent.epsilon}")
>>> print(f"Episodes: {agent.training_history['episodes']}")
```

### View Activities
```bash
python manage.py shell
>>> from workout.models import Activity
>>> activities = Activity.objects.all()
>>> for a in activities:
>>>     print(f"{a.activity_name}: engagement={a.engagement_contribution}")
```

### View Sessions & Metrics
```bash
python manage.py shell
>>> from workout.models import WorkoutSession
>>> session = WorkoutSession.objects.latest('session_date')
>>> print(f"Completion: {session.completion_rate}")
>>> print(f"Avg Motivation Delta: {session.avg_motivation_delta}")
>>> print(f"Engagement: {session.engagement_contribution}")
```

---

## Next Steps After Testing

1. **✓ Tests Pass** → System is ready!
2. Create test data with multiple users
3. Simulate 10-20 activity sessions
4. Watch RL agent Q-values grow
5. Verify activities increase/decrease by difficulty
6. Watch epsilon decay over episodes
7. Celebrate! Your adaptive system works! 🎉
