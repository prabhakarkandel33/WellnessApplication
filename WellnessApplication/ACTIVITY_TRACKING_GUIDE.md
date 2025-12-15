# 🎯 Activity-Based RL Training - Complete Guide

## Understanding the Flow

### Current Problem
Your baseline programs have vague exercises like "Basic stretching routine". This doesn't:
- ❌ Track which specific activities users do
- ❌ Measure completion rates per activity
- ❌ Feed completion data to RL agent
- ❌ Adapt recommendations based on activity performance

### Solution
Create an **Activity Tracking System** that:
1. ✅ Defines specific, concrete activities
2. ✅ Tracks completion per activity
3. ✅ Captures user motivation during activity
4. ✅ Feeds data to RL agent for learning
5. ✅ Improves future recommendations

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                    USER JOURNEY                          │
└──────────────────────────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────┐
        │ GET /recommend/                │
        │ Returns 5-7 specific activities│
        │ for user's segment             │
        └────────┬───────────────────────┘
                 │
                 ▼
    ┌────────────────────────────────────┐
    │ Activity.objects.create()           │
    │ (for tracking)                     │
    └────────────────────────────────────┘
                 │
                 ▼
        ┌──────────────────────┐
        │ User completes       │
        │ activities           │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────────────────┐
        │ POST /activity/complete/          │
        │ {                                │
        │   "activity_id": 123,            │
        │   "completed": true,             │
        │   "motivation_before": 3,        │
        │   "motivation_after": 4,         │
        │   "notes": "Felt great!"         │
        │ }                                │
        └──────────┬───────────────────────┘
                   │
                   ▼
        ┌──────────────────────────────────┐
        │ Update Activity Record            │
        │ Calculate engagement delta        │
        └──────────┬───────────────────────┘
                   │
                   ▼
        ┌──────────────────────────────────┐
        │ POST /feedback/                  │
        │ Feed to RL agent                 │
        │ Update Q-table                   │
        └──────────────────────────────────┘
```

---

## Step 1: Create Activity Model

You'll need a model to track individual activities:

```python
# In workout/models.py (create this file if it doesn't exist)

class Activity(models.Model):
    ACTIVITY_TYPES = [
        ('exercise', 'Exercise'),
        ('meditation', 'Meditation'),
        ('journaling', 'Journaling'),
    ]
    
    # Identifier
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    activity_type = models.CharField(choices=ACTIVITY_TYPES)
    activity_name = models.CharField()  # e.g., "30 Min Jogging"
    
    # Metadata
    segment = models.CharField()  # Which segment this activity is for
    rl_action_id = models.IntegerField()  # Which RL action recommended this
    
    # Details
    description = models.TextField()  # Specific instructions
    duration_minutes = models.IntegerField()
    intensity = models.CharField()  # Low, Medium, High
    
    # Tracking
    assigned_date = models.DateTimeField()
    completion_date = models.DateTimeField(null=True)
    completed = models.BooleanField(default=False)
    
    # Feedback
    motivation_before = models.IntegerField(1-5, null=True)  # Before starting
    motivation_after = models.IntegerField(1-5, null=True)   # After completing
    difficulty_rating = models.IntegerField(1-5, null=True)  # How hard was it?
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
```

---

## Step 2: Create Specific Activity Definitions

Replace vague exercises with concrete ones:

```python
# Activity definitions per segment

ACTIVITIES = {
    "High Anxiety, Low Activity": {
        "physical": [
            {
                "name": "5-Min Gentle Stretching",
                "type": "exercise",
                "duration": 5,
                "intensity": "Low",
                "description": "Neck rolls, shoulder shrugs, wrist circles, hamstring stretches",
                "instructions": [
                    "1. Neck rolls: 10 clockwise, 10 counter-clockwise",
                    "2. Shoulder shrugs: 15 repetitions",
                    "3. Wrist circles: 10 each direction",
                    "4. Hamstring stretches: 30 seconds each leg"
                ]
            },
            {
                "name": "Child's Pose Breathing",
                "type": "exercise",
                "duration": 3,
                "intensity": "Low",
                "description": "Relaxing yoga pose with focused breathing",
                "instructions": [
                    "1. Kneel on yoga mat or soft surface",
                    "2. Sit back on heels, extend arms forward",
                    "3. Rest forehead on mat",
                    "4. Take 10 deep breaths, focusing on exhale"
                ]
            },
            {
                "name": "Walking: 10 Minutes",
                "type": "exercise",
                "duration": 10,
                "intensity": "Low",
                "description": "Slow-paced walking in comfortable environment",
                "instructions": [
                    "1. Choose safe, familiar route",
                    "2. Maintain comfortable pace",
                    "3. Focus on breathing (4-count in, 6-count out)",
                    "4. Optional: outdoor in nature preferred"
                ]
            }
        ],
        "mental": [
            {
                "name": "4-7-8 Breathing Technique",
                "type": "meditation",
                "duration": 5,
                "intensity": "Low",
                "description": "Proven anxiety reduction technique",
                "instructions": [
                    "1. Sit comfortably with good posture",
                    "2. Inhale for count of 4",
                    "3. Hold breath for count of 7",
                    "4. Exhale slowly for count of 8",
                    "5. Repeat 4 times"
                ]
            },
            {
                "name": "Body Scan Meditation",
                "type": "meditation",
                "duration": 10,
                "intensity": "Low",
                "description": "Systematic tension release through awareness",
                "instructions": [
                    "1. Lie flat on back or sit in comfortable chair",
                    "2. Close eyes, take 3 deep breaths",
                    "3. Focus on toes - notice sensations, release tension",
                    "4. Move awareness up: feet, legs, abdomen, chest, arms, shoulders, head",
                    "5. Total 10 minutes, don't rush"
                ]
            }
        ]
    },
    
    "Moderate Anxiety, Moderate Activity": {
        "physical": [
            {
                "name": "Brisk Walking: 20 Minutes",
                "type": "exercise",
                "duration": 20,
                "intensity": "Moderate",
                "description": "Faster-paced walking with heart rate elevation",
                "instructions": [
                    "1. Warm up with 2 minutes slow walking",
                    "2. Walk at pace where conversation is possible but requires effort",
                    "3. Maintain for 15 minutes",
                    "4. Cool down with 3 minutes slow walking"
                ]
            },
            {
                "name": "Bodyweight Circuit: Push-ups, Squats, Planks",
                "type": "exercise",
                "duration": 15,
                "intensity": "Moderate",
                "description": "Compound movements using body weight",
                "instructions": [
                    "1. 8-10 push-ups (wall/incline if needed)",
                    "2. 15 bodyweight squats",
                    "3. 30-second plank",
                    "4. Rest 60 seconds",
                    "5. Repeat 2 more times (3 sets total)"
                ]
            }
        ],
        "mental": [
            {
                "name": "Guided Gratitude Journaling: 10 Minutes",
                "type": "journaling",
                "duration": 10,
                "intensity": "Low",
                "description": "Structured journaling with gratitude focus",
                "instructions": [
                    "1. Find quiet space with paper/pen or device",
                    "2. Write header: 'Today I'm grateful for...'",
                    "3. List 5-7 specific things (events, people, sensations)",
                    "4. For each, write 1-2 sentences WHY you're grateful",
                    "5. Reflect on how this makes you feel"
                ]
            },
            {
                "name": "Mindfulness Meditation: 10 Minutes",
                "type": "meditation",
                "duration": 10,
                "intensity": "Moderate",
                "description": "Focused attention meditation",
                "instructions": [
                    "1. Sit comfortably, eyes closed",
                    "2. Focus attention on breath",
                    "3. Count each exhale from 1-10",
                    "4. When mind wanders, return to 1 without judgment",
                    "5. Continue for 10 minutes"
                ]
            }
        ]
    }
}
```

---

## Step 3: How RL Learns from Activities

```python
# The Loop:

Episode 1 (User with High Anxiety, Low Activity):
├─ System recommends: Action 2 (Increase Meditation)
├─ Recommended activities:
│  ├─ 4-7-8 Breathing (5 min)
│  └─ Body Scan Meditation (10 min)
├─ User completes 4-7-8 Breathing
│  ├─ motivation_before: 2/5
│  └─ motivation_after: 4/5 (+2 increase!)
├─ System calculates:
│  ├─ completion_rate: 50% (1 of 2)
│  ├─ motivation_delta: +0.4 (2/5 = 0.4)
│  └─ engagement_delta: +0.1
└─ RL agent learns: Action 2 → decent reward

Episode 2 (Similar user):
├─ RL agent has learned from Episode 1
├─ Recommends Action 2 again (exploitation)
└─ If user also succeeds, Q-value for Action 2 increases further
```

---

## Step 4: API Design

### Endpoint 1: GET /activity/recommended/
```
Returns activities for user based on RL recommendation

Response:
{
  "rl_action": "Increase Meditation Frequency",
  "reason": "Based on your engagement level and segment",
  "activities": [
    {
      "id": 1,
      "name": "4-7-8 Breathing Technique",
      "type": "meditation",
      "duration_minutes": 5,
      "intensity": "Low",
      "description": "Proven anxiety reduction technique",
      "instructions": [...],
      "motivation_tracking": true  // Can track motivation
    },
    {
      "id": 2,
      "name": "Body Scan Meditation",
      "type": "meditation",
      "duration_minutes": 10,
      "intensity": "Low",
      "description": "Systematic tension release",
      "instructions": [...]
    }
  ]
}
```

### Endpoint 2: POST /activity/{id}/complete/
```
Track activity completion with feedback

Request:
{
  "completed": true,
  "motivation_before": 2,
  "motivation_after": 4,
  "difficulty_rating": 3,
  "notes": "Felt great, will do again"
}

Response:
{
  "status": "success",
  "activity": {...},
  "stats": {
    "total_completed_today": 1,
    "completion_rate": "50%",
    "avg_motivation_increase": 2,
    "engagement_delta": 0.15
  }
}
```

### Endpoint 3: POST /activity/feedback-batch/
```
After completing multiple activities, submit all feedback at once

Request:
{
  "activities": [
    {
      "activity_id": 1,
      "completed": true,
      "motivation_before": 2,
      "motivation_after": 4
    },
    {
      "activity_id": 2,
      "completed": false,
      "motivation_before": 2,
      "motivation_after": 2
    }
  ],
  "overall_session_rating": 4,
  "notes": "Good workout, tired now"
}

Response:
{
  "status": "success",
  "activities_updated": 2,
  "engagement_delta": 0.2,
  "rl_reward_signal": 0.45,
  "training_metrics": {
    "total_episodes": 15,
    "epsilon": 0.27
  }
}
```

---

## Step 5: What RL Agent Learns

The agent observes:

```
Activity Performance Data:
├─ Activity Name
├─ User Motivation Before (1-5)
├─ User Motivation After (1-5)
├─ Completed? (Y/N)
├─ Difficulty Rating (1-5)
└─ User Notes (optional)

Aggregated to:
├─ engagement_score (completion rate over time)
├─ motivation_score (motivation change)
└─ specific_action_effectiveness

RL Agent Optimizes:
├─ "Action 0 is good for this segment" (high completion)
├─ "Action 2 causes motivation boost" (motivation_after > before)
├─ "Action 4 is bad for dropouts" (low completion rate)
└─ Continuously adjusts Q-values
```

---

## Testing Strategy

### Test 1: Unit Test Activity Model
```python
def test_activity_creation():
    activity = Activity.objects.create(
        user=user,
        activity_name="5-Min Stretch",
        duration_minutes=5,
        intensity="Low"
    )
    assert activity.completed == False
    assert activity.motivation_before is None
```

### Test 2: API Test - Get Recommendations
```python
def test_get_recommended_activities():
    response = client.get('/activity/recommended/')
    assert response.status_code == 200
    assert 'activities' in response.json()
    assert len(response.json()['activities']) > 0
```

### Test 3: API Test - Complete Activity
```python
def test_complete_activity():
    activity = Activity.objects.create(...)
    
    response = client.post(f'/activity/{activity.id}/complete/', {
        "completed": True,
        "motivation_before": 2,
        "motivation_after": 4,
        "difficulty_rating": 3
    })
    
    assert response.status_code == 200
    activity.refresh_from_db()
    assert activity.completed == True
    assert activity.motivation_after == 4
```

### Test 4: RL Learning Test
```python
def test_rl_learns_from_activities():
    # Create 10 similar users
    for i in range(10):
        user = create_user(segment="High Anxiety, Low Activity")
        activities = get_recommended_activities(user)
        
        # All users complete the activities
        for activity in activities:
            complete_activity(activity, motivation_before=2, motivation_after=4)
    
    # Check that RL agent improved Q-values for successful action
    agent = load_rl_agent()
    assert agent.epsilon < initial_epsilon
    assert agent.training_history['episodes'] >= 10
```

### Test 5: End-to-End Flow Test
```python
def test_complete_user_journey():
    # 1. User gets recommendation
    response = client.get('/activity/recommended/')
    activities = response.json()['activities']
    
    # 2. User completes all activities
    for activity in activities:
        response = client.post(f'/activity/{activity["id"]}/complete/', {
            "completed": True,
            "motivation_before": 2,
            "motivation_after": 4
        })
        assert response.status_code == 200
    
    # 3. Submit batch feedback
    response = client.post('/activity/feedback-batch/', {...})
    assert response.status_code == 200
    
    # 4. Check engagement increased
    user.refresh_from_db()
    assert user.engagement_score > initial_engagement
    
    # 5. Next recommendation should be better
    response2 = client.get('/activity/recommended/')
    assert response2.json()['rl_action'] != response.json()['rl_action']
```

---

## Implementation Checklist

- [ ] Create `workout/models.py` with Activity model
- [ ] Create migration for Activity model
- [ ] Replace vague exercises with ACTIVITIES dict (concrete activities)
- [ ] Create `ActivityView` for GET /activity/recommended/
- [ ] Create `CompleteActivityView` for POST /activity/{id}/complete/
- [ ] Create `ActivityFeedbackBatchView` for POST /activity/feedback-batch/
- [ ] Integrate activity completion with RL feedback
- [ ] Write unit tests for Activity model
- [ ] Write API tests for all 3 endpoints
- [ ] Write integration test for full user journey
- [ ] Test RL agent learning from activity data

---

This is the complete architecture. Ready to implement? Let me know and I'll build it!
