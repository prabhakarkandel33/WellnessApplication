# RL Agent Setup & Next Steps

## ✅ What Was Just Implemented

### Core Components
1. **RL Agent Module** (`api/rl_agent.py`)
   - `WellnessRLAgent`: Q-learning agent with 6 actions
   - `RLModelManager`: Handles model persistence

2. **Enhanced User Model** (`api/models.py`)
   - Added 6 new fields for engagement tracking
   - Migration file ready: `0003_rl_agent_fields.py`

3. **Updated Views** (`workout/views.py`)
   - `RecommendProgram`: GET returns RL-optimized recommendations, POST collects feedback
   - `EngagementFeedback`: New dedicated feedback endpoint

4. **URL Routes** (`workout/urls.py`)
   - `/recommend/` - GET/POST for recommendations
   - `/feedback/` - POST for feedback collection

## 📋 Setup Instructions

### Step 1: Create Models Directory
```bash
mkdir -p api/models
```

### Step 2: Apply Database Migration
```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 3: Test the Integration

#### Get a Recommendation
```bash
curl -X GET http://localhost:8000/workout/recommend/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Submit Feedback
```bash
curl -X POST http://localhost:8000/workout/feedback/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "engagement_delta": 0.1,
    "workout_completed": true,
    "meditation_completed": true,
    "feedback_rating": 4
  }'
```

## 🎯 Key Features

| Feature | Details |
|---------|---------|
| **State Representation** | 7D discrete state (age, gender, BMI, anxiety, activity, engagement, segment) |
| **Action Space** | 6 actions (intensity ±, meditation freq, motivation, journaling, maintain) |
| **Reward Function** | $R = 0.5E + 0.3M - 1.0D$ (engagement + motivation - dropout) |
| **Learning Algorithm** | Q-learning with ε-greedy exploration |
| **Persistence** | Q-table saved to `api/models/wellness_rl_agent.json` |
| **Training Trigger** | Automatic on each feedback submission |

## 📊 Typical Data Flow

```
1. User requests recommendation
   ↓
2. System extracts user state (age, anxiety, activity, etc.)
   ↓
3. RL agent selects best action using Q-table
   ↓
4. Baseline program modified based on action
   ↓
5. Recommendation returned to user
   ↓
6. User completes activity and provides feedback
   ↓
7. Feedback triggers Q-table update
   ↓
8. Model saved for next user session
```

## 🔧 Configuration Options

**In `api/rl_agent.py`**, adjust these parameters:

```python
WellnessRLAgent(
    learning_rate=0.1,          # How fast agent learns (higher = faster)
    discount_factor=0.9,        # Future reward importance
    initial_epsilon=0.3,        # Initial exploration rate
    epsilon_decay=0.995,        # How fast to reduce exploration
    min_epsilon=0.05            # Minimum exploration rate
)
```

**Reward weights:**
```python
self.alpha = 0.5              # Engagement importance
self.beta = 0.3               # Motivation importance
self.lambda_penalty = 1.0     # Dropout penalty
```

## 📈 Monitoring Agent Performance

Check the response from any feedback:
```json
"training_metrics": {
  "reward_signal": 0.35,      // Last reward value
  "action_trained": 2,        // Last action (0-5)
  "agent_epsilon": 0.18,      // Current exploration %
  "total_episodes": 42        // Total training updates
}
```

**What to expect:**
- **Episodes 1-20**: High variance, agent explores randomly
- **Episodes 20-100**: Agent starts converging to patterns
- **Episodes 100+**: Stable, mostly exploiting learned policy
- **Epsilon ~0.05**: Agent mostly using learned Q-values

## ⚠️ Important Notes

1. **First Request**: Creates `api/models/wellness_rl_agent.json` automatically
2. **User Fields**: Missing user data uses safe defaults (age=30, BMI=25)
3. **Model Saving**: Happens after every feedback (can batch if needed for performance)
4. **Segment Mapping**: Must match your `SEGMENT_CHOICES` in models.py
5. **Thread Safety**: Q-table updates are not atomic (use Redis for distributed systems)

## 🐛 Debugging

**Check if models directory was created:**
```bash
ls -la api/models/
```

**Verify Q-table is saving:**
```bash
cat api/models/wellness_rl_agent.json | python -m json.tool
```

**Test agent directly:**
```python
from api.rl_agent import RLModelManager

manager = RLModelManager()
agent = manager.load_agent()

user_state = {
    'age': 25,
    'gender': 0,
    'bmi': 24,
    'anxiety_score': 8,
    'activity_week': 3,
    'engagement': 0.5,
    'motivation': 3,
    'segment': 'Wellness Seekers'
}

action = agent.select_action(user_state)
print(f"Recommended action: {agent.get_action_name(action)}")
```

## 🚀 Next Steps

1. ✅ Run migrations to update database
2. ✅ Test `/recommend/` endpoint
3. ✅ Submit feedback via `/feedback/` endpoint
4. Monitor Q-table growth in `api/models/wellness_rl_agent.json`
5. Analyze user engagement patterns
6. (Optional) Fine-tune hyperparameters based on results

## 📚 Documentation

Full documentation: See `RL_IMPLEMENTATION_GUIDE.md` for:
- Detailed algorithm explanation
- State encoding details
- Reward function derivation
- Future enhancement ideas
- Troubleshooting guide
