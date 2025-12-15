# 🧪 Complete Testing Guide for Activity-Based RL System

## Testing Overview

You'll test at 3 levels:
1. **Unit Tests** - Test individual components
2. **Integration Tests** - Test how Activity model works with RL
3. **End-to-End Tests** - Test complete user journey

---

## Part 1: Unit Tests (Testing Activities Model)

### Test File: `workout/tests.py`

```python
from django.test import TestCase
from django.utils import timezone
from api.models import CustomUser
from workout.models import Activity, WorkoutSession
from datetime import timedelta


class ActivityModelTests(TestCase):
    """Test the Activity model"""
    
    def setUp(self):
        """Create test user and activity before each test"""
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
    
    def test_activity_creation(self):
        """Test that we can create an activity"""
        activity = Activity.objects.create(
            user=self.user,
            activity_name="5-Min Gentle Stretching",
            activity_type="exercise",
            user_segment="High Anxiety, Low Activity",
            description="Gentle stretching routine",
            duration_minutes=5,
            intensity="Low",
            instructions=["Step 1", "Step 2", "Step 3"]
        )
        
        self.assertEqual(activity.activity_name, "5-Min Gentle Stretching")
        self.assertEqual(activity.user, self.user)
        self.assertFalse(activity.completed)
        self.assertIsNone(activity.motivation_before)
    
    def test_activity_completion_with_motivation(self):
        """Test recording completion and motivation data"""
        activity = Activity.objects.create(
            user=self.user,
            activity_name="Meditation",
            activity_type="meditation",
            user_segment="High Anxiety, Low Activity",
            description="Body scan meditation",
            duration_minutes=10,
            intensity="Low"
        )
        
        # Mark as completed
        activity.completed = True
        activity.completion_date = timezone.now()
        activity.motivation_before = 2
        activity.motivation_after = 4
        activity.save()
        
        # Check calculated fields
        self.assertTrue(activity.completed)
        self.assertEqual(activity.motivation_delta, 2)
        self.assertTrue(activity.is_motivating)
    
    def test_motivation_not_motivating(self):
        """Test when motivation decreases"""
        activity = Activity.objects.create(
            user=self.user,
            activity_name="Hard Workout",
            activity_type="exercise",
            user_segment="Low Anxiety, High Activity",
            description="Intense workout",
            duration_minutes=30,
            intensity="High"
        )
        
        activity.completed = True
        activity.motivation_before = 4
        activity.motivation_after = 3
        activity.save()
        
        self.assertEqual(activity.motivation_delta, -1)
        self.assertFalse(activity.is_motivating)
    
    def test_engagement_contribution_complete_and_motivating(self):
        """Test engagement contribution calculation"""
        activity = Activity.objects.create(
            user=self.user,
            activity_name="Yoga",
            activity_type="exercise",
            user_segment="High Anxiety, Low Activity",
            description="Yoga session",
            duration_minutes=20,
            intensity="Low"
        )
        
        # Completed, motivating, enjoyable
        activity.completed = True
        activity.motivation_before = 2
        activity.motivation_after = 5
        activity.enjoyment_rating = 5
        activity.save()
        
        engagement = activity.engagement_contribution
        self.assertGreater(engagement, 0.8)  # Should be high
        self.assertLessEqual(engagement, 1.0)
    
    def test_engagement_contribution_incomplete(self):
        """Test penalty for incomplete activity"""
        activity = Activity.objects.create(
            user=self.user,
            activity_name="Workout",
            activity_type="exercise",
            user_segment="High Anxiety, Low Activity",
            description="Incomplete workout",
            duration_minutes=15,
            intensity="Low",
            completed=False
        )
        
        engagement = activity.engagement_contribution
        self.assertEqual(engagement, -0.1)  # Penalty
    
    def test_activity_instructions_as_list(self):
        """Test that instructions are stored as JSON list"""
        instructions = [
            "Step 1: Start slowly",
            "Step 2: Breathe deeply",
            "Step 3: Relax completely"
        ]
        
        activity = Activity.objects.create(
            user=self.user,
            activity_name="Meditation",
            activity_type="meditation",
            user_segment="High Anxiety, Low Activity",
            description="Guided meditation",
            duration_minutes=10,
            intensity="Low",
            instructions=instructions
        )
        
        self.assertEqual(activity.instructions, instructions)
        self.assertEqual(len(activity.instructions), 3)


class WorkoutSessionTests(TestCase):
    """Test the WorkoutSession model"""
    
    def setUp(self):
        """Create test user and activities"""
        self.user = CustomUser.objects.create_user(
            username='testuser2',
            email='test2@test.com',
            password='testpass123'
        )
        
        # Create multiple activities
        self.activity1 = Activity.objects.create(
            user=self.user,
            activity_name="Stretching",
            activity_type="exercise",
            user_segment="Moderate Anxiety, Moderate Activity",
            description="Stretch",
            duration_minutes=5,
            intensity="Low"
        )
        
        self.activity2 = Activity.objects.create(
            user=self.user,
            activity_name="Walking",
            activity_type="exercise",
            user_segment="Moderate Anxiety, Moderate Activity",
            description="Walk",
            duration_minutes=20,
            intensity="Moderate"
        )
    
    def test_session_creation(self):
        """Test creating a workout session"""
        session = WorkoutSession.objects.create(
            user=self.user,
            session_type='daily'
        )
        session.activities.add(self.activity1, self.activity2)
        
        self.assertEqual(session.activities.count(), 2)
        self.assertEqual(session.user, self.user)
    
    def test_calculate_metrics_with_completions(self):
        """Test session metrics calculation"""
        session = WorkoutSession.objects.create(
            user=self.user,
            session_type='daily'
        )
        session.activities.add(self.activity1, self.activity2)
        
        # Mark first activity as completed
        self.activity1.completed = True
        self.activity1.motivation_before = 2
        self.activity1.motivation_after = 4
        self.activity1.save()
        
        # Don't complete second activity
        self.activity2.completed = False
        self.activity2.save()
        
        # Calculate metrics
        session.calculate_metrics()
        
        self.assertEqual(session.total_activities, 2)
        self.assertEqual(session.completed_activities, 1)
        self.assertEqual(session.completion_rate, 0.5)
        self.assertEqual(session.avg_motivation_delta, 2.0)
    
    def test_session_engagement_contribution(self):
        """Test session engagement contribution"""
        session = WorkoutSession.objects.create(
            user=self.user,
            session_type='daily',
            completion_rate=0.8,
            avg_motivation_delta=1.5,
            overall_session_rating=5
        )
        
        engagement = session.engagement_contribution
        self.assertGreater(engagement, 0.4)
        self.assertLessEqual(engagement, 1.0)

```

### How to Run Unit Tests

```bash
# Run all tests
python manage.py test workout.tests

# Run specific test class
python manage.py test workout.tests.ActivityModelTests

# Run specific test
python manage.py test workout.tests.ActivityModelTests.test_activity_creation

# Run with verbosity
python manage.py test workout.tests -v 2

# Run and see print statements
python manage.py test workout.tests --pdb
```

---

## Part 2: Integration Tests (Testing with RL Agent)

### Test File: `workout/test_rl_integration.py`

```python
from django.test import TestCase
from api.models import CustomUser
from workout.models import Activity
from api.rl_agent import RLModelManager, WellnessRLAgent


class ActivityRLIntegrationTests(TestCase):
    """Test how Activity data feeds into RL agent"""
    
    def setUp(self):
        """Create test user and RL agent"""
        self.user = CustomUser.objects.create_user(
            username='rl_test_user',
            email='rl@test.com',
            password='testpass123',
            age=30,
            gender='male',
            gad7_score=8,
            physical_activity_week=3,
            engagement_score=0.5,
            motivation_score=3,
            segment_label=0  # High Anxiety, Low Activity
        )
        
        self.rl_manager = RLModelManager(model_dir='test_models')
        self.rl_agent = self.rl_manager.load_agent()
    
    def test_activity_completion_affects_engagement(self):
        """Test that completing activities updates user engagement"""
        initial_engagement = self.user.engagement_score
        
        # Create and complete activity
        activity = Activity.objects.create(
            user=self.user,
            activity_name="Meditation",
            activity_type="meditation",
            user_segment="High Anxiety, Low Activity",
            description="Body scan",
            duration_minutes=10,
            intensity="Low"
        )
        
        activity.completed = True
        activity.motivation_before = 2
        activity.motivation_after = 4
        activity.enjoyment_rating = 5
        activity.save()
        
        # Simulate updating user engagement from activity
        engagement_delta = activity.engagement_contribution
        self.user.engagement_score = max(0, min(1, self.user.engagement_score + engagement_delta))
        self.user.save()
        
        self.assertGreater(self.user.engagement_score, initial_engagement)
    
    def test_rl_agent_learns_from_activity_feedback(self):
        """Test RL agent Q-value updates from activity completion"""
        # Get initial Q-table size
        initial_q_table_size = len(self.rl_agent.q_table)
        
        # Create user state
        user_state = {
            'age': self.user.age,
            'gender': 0,  # Male
            'bmi': 25,
            'anxiety_score': self.user.gad7_score,
            'activity_week': self.user.physical_activity_week,
            'engagement': self.user.engagement_score,
            'motivation': self.user.motivation_score,
            'segment': 'High Anxiety, Low Activity'
        }
        
        # Agent selects action
        action = self.rl_agent.select_action(user_state)
        self.assertIn(action, range(6))  # Should be 0-5
        
        # Simulate activity completion with positive feedback
        new_engagement = 0.7  # Improved
        new_motivation = 5  # Happy
        
        new_state = user_state.copy()
        new_state['engagement'] = new_engagement
        new_state['motivation'] = new_motivation
        
        # Calculate reward
        reward = self.rl_agent.calculate_reward(new_state, action)
        self.assertGreater(reward, 0)  # Should be positive
        
        # Update Q-table
        self.rl_agent.update_q_value(user_state, action, reward, new_state)
        
        # Check that Q-table grew
        self.assertGreaterEqual(len(self.rl_agent.q_table), initial_q_table_size)
    
    def test_multiple_activity_completions_improve_rl(self):
        """Test that multiple successful activities improve RL recommendations"""
        initial_epsilon = self.rl_agent.epsilon
        
        # Simulate 5 activity completions
        for i in range(5):
            activity = Activity.objects.create(
                user=self.user,
                activity_name=f"Activity {i+1}",
                activity_type="exercise",
                user_segment="High Anxiety, Low Activity",
                description="Test activity",
                duration_minutes=10,
                intensity="Low"
            )
            
            # Mark as successful
            activity.completed = True
            activity.motivation_before = 2 + i
            activity.motivation_after = 4 + i
            activity.enjoyment_rating = 5
            activity.save()
            
            # Update RL
            self.user.engagement_score += 0.1
            self.user.motivation_score = 4
            self.user.save()
            
            # Train RL
            user_state = {
                'age': self.user.age,
                'gender': 0,
                'bmi': 25,
                'anxiety_score': self.user.gad7_score,
                'activity_week': self.user.physical_activity_week,
                'engagement': self.user.engagement_score - 0.1,
                'motivation': 3,
                'segment': 'High Anxiety, Low Activity'
            }
            
            new_state = user_state.copy()
            new_state['engagement'] = self.user.engagement_score
            new_state['motivation'] = self.user.motivation_score
            
            action = self.rl_agent.select_action(user_state)
            reward = self.rl_agent.calculate_reward(new_state, action)
            self.rl_agent.update_q_value(user_state, action, reward, new_state)
            self.rl_agent.decay_epsilon()
        
        # Epsilon should have decayed
        self.assertLess(self.rl_agent.epsilon, initial_epsilon)
        
        # Training history should show episodes
        self.assertGreater(self.rl_agent.training_history['episodes'], 0)

```

### How to Run Integration Tests

```bash
python manage.py test workout.test_rl_integration -v 2
```

---

## Part 3: End-to-End API Tests (Testing Complete Flow)

### Test File: `workout/test_api.py`

```python
from django.test import Client, TestCase
from django.contrib.auth.models import User
from api.models import CustomUser
from workout.models import Activity, WorkoutSession
from rest_framework.test import APIClient, APITestCase
from rest_framework.authtoken.models import Token


class ActivityAPIEndToEndTests(APITestCase):
    """Test complete API flow from recommendation to feedback"""
    
    def setUp(self):
        """Create test user and authenticate"""
        self.user = CustomUser.objects.create_user(
            username='apitest',
            email='apitest@test.com',
            password='testpass123',
            age=35,
            gender='female',
            gad7_score=12,
            physical_activity_week=2,
            engagement_score=0.4,
            motivation_score=3,
            segment_label=0  # High Anxiety, Low Activity
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_recommend_activities_endpoint(self):
        """Test GET /activity/recommended/ endpoint"""
        response = self.client.get('/workout/activity/recommended/')
        
        # Should return 200
        self.assertEqual(response.status_code, 200)
        
        # Response should contain activities
        data = response.json()
        self.assertIn('activities', data)
        self.assertGreater(len(data['activities']), 0)
        
        # Each activity should have required fields
        for activity in data['activities']:
            self.assertIn('id', activity)
            self.assertIn('name', activity)
            self.assertIn('type', activity)
            self.assertIn('duration_minutes', activity)
            self.assertIn('instructions', activity)
            self.assertIn('intensity', activity)
    
    def test_complete_activity_endpoint(self):
        """Test POST /activity/{id}/complete/ endpoint"""
        # Create an activity
        activity = Activity.objects.create(
            user=self.user,
            activity_name="Test Activity",
            activity_type="exercise",
            user_segment="High Anxiety, Low Activity",
            description="Test",
            duration_minutes=5,
            intensity="Low"
        )
        
        # Complete the activity
        response = self.client.post(
            f'/workout/activity/{activity.id}/complete/',
            {
                'completed': True,
                'motivation_before': 2,
                'motivation_after': 4,
                'difficulty_rating': 2,
                'enjoyment_rating': 4,
                'notes': 'Felt good!'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Check activity was updated
        activity.refresh_from_db()
        self.assertTrue(activity.completed)
        self.assertEqual(activity.motivation_before, 2)
        self.assertEqual(activity.motivation_after, 4)
        self.assertEqual(activity.enjoyment_rating, 4)
    
    def test_activity_feedback_batch_endpoint(self):
        """Test POST /activity/feedback-batch/ endpoint"""
        # Create multiple activities
        activities = []
        for i in range(3):
            activity = Activity.objects.create(
                user=self.user,
                activity_name=f"Activity {i}",
                activity_type="exercise",
                user_segment="High Anxiety, Low Activity",
                description="Test",
                duration_minutes=10,
                intensity="Low"
            )
            activities.append(activity)
        
        # Submit batch feedback
        response = self.client.post(
            '/workout/activity/feedback-batch/',
            {
                'activities': [
                    {
                        'activity_id': activities[0].id,
                        'completed': True,
                        'motivation_before': 2,
                        'motivation_after': 4
                    },
                    {
                        'activity_id': activities[1].id,
                        'completed': True,
                        'motivation_before': 3,
                        'motivation_after': 5
                    },
                    {
                        'activity_id': activities[2].id,
                        'completed': False,
                        'motivation_before': 2,
                        'motivation_after': 2
                    }
                ],
                'overall_session_rating': 4,
                'notes': 'Good session overall'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('engagement_delta', data)
        self.assertIn('rl_reward_signal', data)
        
        # Check user engagement updated
        self.user.refresh_from_db()
        self.assertGreater(self.user.engagement_score, 0.4)
    
    def test_complete_user_journey(self):
        """Test full flow: recommend -> complete -> batch feedback -> RL training"""
        # Step 1: Get recommended activities
        response = self.client.get('/workout/activity/recommended/')
        self.assertEqual(response.status_code, 200)
        
        recommended_activity_ids = [
            a['id'] for a in response.json()['activities'][:2]
        ]
        
        # Step 2: Complete each activity
        feedback_list = []
        for i, activity_id in enumerate(recommended_activity_ids):
            response = self.client.post(
                f'/workout/activity/{activity_id}/complete/',
                {
                    'completed': True,
                    'motivation_before': 2 + i,
                    'motivation_after': 4 + i,
                    'difficulty_rating': 2,
                    'enjoyment_rating': 4 + i
                },
                format='json'
            )
            self.assertEqual(response.status_code, 200)
            
            feedback_list.append({
                'activity_id': activity_id,
                'completed': True,
                'motivation_before': 2 + i,
                'motivation_after': 4 + i
            })
        
        # Step 3: Submit batch feedback
        response = self.client.post(
            '/workout/activity/feedback-batch/',
            {
                'activities': feedback_list,
                'overall_session_rating': 5
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['status'], 'success')
        
        # Step 4: Check RL agent was trained
        self.assertGreater(
            data['training_metrics']['total_episodes'],
            0
        )
        
        # Step 5: Check user engagement improved
        self.user.refresh_from_db()
        self.assertGreater(self.user.engagement_score, 0.4)

```

### How to Run API Tests

```bash
python manage.py test workout.test_api -v 2
```

---

## Part 4: Manual Testing with Curl/Postman

### 4.1 Test GET /activity/recommended/

```bash
curl -X GET http://localhost:8000/workout/activity/recommended/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Accept: application/json"
```

**Expected Response:**
```json
{
  "rl_action": "Increase Meditation Frequency",
  "reason": "...",
  "activities": [
    {
      "id": 1,
      "name": "4-7-8 Breathing Technique",
      "type": "meditation",
      "duration_minutes": 5,
      "intensity": "Low",
      "description": "...",
      "instructions": ["Step 1", "Step 2", ...]
    },
    {
      "id": 2,
      "name": "Body Scan Meditation",
      ...
    }
  ]
}
```

### 4.2 Test POST /activity/{id}/complete/

```bash
curl -X POST http://localhost:8000/workout/activity/1/complete/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "completed": true,
    "motivation_before": 2,
    "motivation_after": 4,
    "difficulty_rating": 2,
    "enjoyment_rating": 4,
    "notes": "Felt great!"
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "activity": {...},
  "stats": {
    "completion_rate": "50%",
    "engagement_delta": 0.15
  }
}
```

### 4.3 Test POST /activity/feedback-batch/

```bash
curl -X POST http://localhost:8000/workout/activity/feedback-batch/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
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
    "notes": "Good workout"
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "engagement_delta": 0.2,
  "rl_reward_signal": 0.45,
  "training_metrics": {
    "total_episodes": 15,
    "epsilon": 0.27
  }
}
```

---

## Part 5: Testing RL Learning

### Manual Test: Verify Q-Table Growth

```python
# In Django shell
python manage.py shell

# Check Q-table size
from api.rl_agent import RLModelManager
manager = RLModelManager()
agent = manager.load_agent()

print(f"Q-table entries: {len(agent.q_table)}")
print(f"Epsilon: {agent.epsilon}")
print(f"Total episodes trained: {agent.training_history['episodes']}")

# Print first few Q-values
for i, (state, actions) in enumerate(list(agent.q_table.items())[:3]):
    print(f"State {state}: {dict(actions)}")
    if i > 2:
        break
```

### Full Learning Test Script

```python
# test_rl_learning.py - Run this to see RL learning in action

from api.models import CustomUser
from workout.models import Activity
from api.rl_agent import RLModelManager

# Create test user
user = CustomUser.objects.create_user(
    username='rl_test',
    email='rl@test.com',
    password='test123',
    segment_label=0,  # High Anxiety, Low Activity
    engagement_score=0.5,
    motivation_score=3
)

# Create RL agent
manager = RLModelManager()
agent = manager.load_agent()

# Simulate 10 user sessions
for session_num in range(10):
    print(f"\n--- Session {session_num + 1} ---")
    
    # Create user state
    user_state = {
        'age': 30,
        'gender': 0,
        'bmi': 25,
        'anxiety_score': 10,
        'activity_week': 3,
        'engagement': user.engagement_score,
        'motivation': user.motivation_score,
        'segment': 'High Anxiety, Low Activity'
    }
    
    # Agent selects action
    action = agent.select_action(user_state)
    print(f"Selected action: {agent.get_action_name(action)}")
    
    # Simulate activity completion
    user.engagement_score += 0.1
    user.motivation_score = min(5, user.motivation_score + 1)
    user.save()
    
    # Create updated state
    new_state = user_state.copy()
    new_state['engagement'] = user.engagement_score
    new_state['motivation'] = user.motivation_score
    
    # Calculate reward
    reward = agent.calculate_reward(new_state, action)
    print(f"Reward: {reward:.3f}")
    
    # Update Q-table
    agent.update_q_value(user_state, action, reward, new_state)
    agent.decay_epsilon()
    
    # Show progress
    print(f"Epsilon: {agent.epsilon:.3f}")
    print(f"Q-table size: {len(agent.q_table)}")
    print(f"Total reward: {agent.training_history['total_reward']:.2f}")
    
    # Save model
    manager.save_agent(agent)

print("\n✅ RL Learning Test Complete!")
print(f"Final epsilon: {agent.epsilon:.3f}")
print(f"Total episodes: {agent.training_history['episodes']}")
```

---

## Summary: Testing Checklist

- [ ] Run all unit tests: `python manage.py test workout.tests`
- [ ] Run RL integration tests: `python manage.py test workout.test_rl_integration`
- [ ] Run API tests: `python manage.py test workout.test_api`
- [ ] Manually test with curl/Postman
- [ ] Verify Q-table grows: `python manage.py shell`
- [ ] Run full learning test script
- [ ] Check epsilon decays properly
- [ ] Verify engagement scores increase over time
- [ ] Confirm activity completion records correctly
- [ ] Test motivation delta calculation

**Total Testing Time: ~1-2 hours**
