"""
Reinforcement Learning Agent for Personalized Wellness Application
Based on the project proposal methodology
"""

import numpy as np
import json
import os
from collections import defaultdict


class WellnessRLAgent:
    """
    Reinforcement Learning Agent for Personalized Wellness Application
    Using Q-learning to optimize program recommendations
    """
    
    def __init__(self, learning_rate=0.1, discount_factor=0.9, 
                 initial_epsilon=0.3, epsilon_decay=0.995, min_epsilon=0.05):
        """
        Initialize RL Agent with Q-learning parameters
        
        Args:
            learning_rate: Controls how much new information updates Q-values
            discount_factor: How much future rewards are valued
            initial_epsilon: Initial exploration rate
            epsilon_decay: Rate at which exploration decreases
            min_epsilon: Minimum exploration rate
        """
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = initial_epsilon
        self.epsilon_decay = epsilon_decay
        self.min_epsilon = min_epsilon
        
        # Q-table: (state) -> {action: Q-value}
        self.q_table = defaultdict(lambda: defaultdict(float))
        
        # Action space - 6 recommended actions
        self.actions = {
            0: "Increase Workout Intensity (IWI)",
            1: "Decrease Workout Intensity (DWI)", 
            2: "Increase Meditation Frequency (IMF)",
            3: "Send Motivational Message (SMM)",
            4: "Introduce Journaling Feature (IJF)",
            5: "Maintain Current Plan (MCP)"
        }
        
        # Reward function weights
        self.alpha = 0.5  # Engagement weight
        self.beta = 0.3   # Motivation weight
        self.lambda_penalty = 1.0  # Dropout penalty
        
        # Training history
        self.training_history = {
            'episodes': 0,
            'total_reward': 0,
            'epsilon_current': self.epsilon
        }

    def encode_state(self, user_state):
        """
        Convert user state to discrete state representation for Q-table
        
        Args:
            user_state: dict with keys:
                - age: int
                - gender: int (0=M, 1=F)
                - bmi: float
                - anxiety_score: int (0-20, GAD-7)
                - activity_week: int (0-7 days)
                - engagement: float (0-1)
                - segment: str (user segment label)
        
        Returns:
            tuple: discrete state representation for Q-table lookup
        """
        age_bin = min(int(user_state.get('age', 30) // 10), 5)
        gender = int(user_state.get('gender', 0))
        bmi = user_state.get('bmi', 25)
        bmi_bin = min(int((bmi - 15) // 5), 6)
        
        anxiety = user_state.get('anxiety_score', 10)
        anxiety_bin = min(int(anxiety // 5), 4)
        
        activity = user_state.get('activity_week', 3)
        activity_bin = min(int(activity), 7)
        
        engagement = user_state.get('engagement', 0.5)
        engagement_bin = min(int(engagement * 10), 10)
        
        # Include segment for better state representation
        segment_map = {
            "High Anxiety, Low Activity": 0,
            "Moderate Anxiety, Moderate Activity": 1,
            "Low Anxiety, High Activity": 2,
            "Physical Health Risk": 3,
            "Wellness Seekers": 4,
            "Inactive, Unengaged": 5
        }
        segment_id = segment_map.get(user_state.get('segment', 'Wellness Seekers'), 4)
        
        return (age_bin, gender, bmi_bin, anxiety_bin, activity_bin, engagement_bin, segment_id)

    def calculate_reward(self, user_state_after, action_taken):
        """
        Calculate reward based on the reward function from proposal:
        R(s,a) = α·E(s') + β·M(s') - λ·D(s')
        
        Args:
            user_state_after: user state after action
            action_taken: which action was taken
        
        Returns:
            float: reward value
        """
        engagement = user_state_after.get('engagement', 0.5)
        motivation = user_state_after.get('motivation', 3) / 5.0  # Normalize to [0,1]
        dropout = 1 if engagement < 0.1 else 0  # Dropout penalty if very low engagement
        
        reward = (self.alpha * engagement + 
                 self.beta * motivation -
                 self.lambda_penalty * dropout)
        
        return reward

    def select_action(self, state_dict):
        """
        ε-greedy action selection
        
        Args:
            state_dict: user state dictionary
        
        Returns:
            int: action index to take
        """
        if np.random.random() < self.epsilon:
            # Exploration: random action
            return np.random.choice(len(self.actions))
        else:
            # Exploitation: best known action for this state
            state_key = self.encode_state(state_dict)
            q_values = [self.q_table[state_key].get(action, 0) for action in range(len(self.actions))]
            return np.argmax(q_values) if max(q_values) > 0 else np.random.choice(len(self.actions))

    def update_q_value(self, state_dict, action, reward, next_state_dict):
        """
        Q-learning update rule:
        Q(s,a) ← Q(s,a) + η[r + γ·max_a'Q(s',a') - Q(s,a)]
        
        Args:
            state_dict: current user state
            action: action taken
            reward: reward received
            next_state_dict: resulting user state
        """
        state_key = self.encode_state(state_dict)
        next_state_key = self.encode_state(next_state_dict)
        
        # Current Q-value
        current_q = self.q_table[state_key].get(action, 0)
        
        # Best next Q-value
        next_q_values = [self.q_table[next_state_key].get(a, 0) for a in range(len(self.actions))]
        max_next_q = max(next_q_values) if next_q_values else 0
        
        # Q-learning update
        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_next_q - current_q
        )
        
        self.q_table[state_key][action] = new_q
        
        # Update training history
        self.training_history['total_reward'] += reward
        self.training_history['episodes'] += 1

    def decay_epsilon(self):
        """Decay exploration rate after each episode"""
        self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)
        self.training_history['epsilon_current'] = self.epsilon

    def get_action_name(self, action_id):
        """Get human-readable action name"""
        return self.actions.get(action_id, "Unknown Action")

    def get_q_table_dict(self):
        """Convert Q-table to serializable format"""
        return {str(k): dict(v) for k, v in self.q_table.items()}

    def load_q_table_dict(self, q_dict):
        """Load Q-table from serializable format"""
        for state_str, actions in q_dict.items():
            # Convert string keys back to tuples
            state_tuple = eval(state_str)
            self.q_table[state_tuple] = defaultdict(float, actions)

    def adjust_activity_difficulty(self, activity, engagement_contribution, recent_completions):
        """
        Dynamically adjust activity duration/reps based on user engagement
        
        Args:
            activity: dict with 'duration', 'instructions', etc.
            engagement_contribution: float (0-1) from previous session
            recent_completions: list of recent engagement scores
        
        Returns:
            dict: adjusted activity with modified duration/instructions
        """
        adjusted = activity.copy()
        
        # Calculate trend from recent engagement
        if recent_completions:
            avg_engagement = sum(recent_completions[-5:]) / len(recent_completions[-5:])
        else:
            avg_engagement = engagement_contribution
        
        # Adjust duration based on engagement
        if avg_engagement > 0.7:
            # User doing well - increase difficulty
            adjusted['duration'] = int(activity.get('duration', 10) * 1.15)
            adjusted['intensity_adjustment'] = "Increased"
            adjusted['reps_adjustment'] = "Add 2-3 more reps per set"
        elif avg_engagement < 0.3:
            # User struggling - decrease difficulty
            adjusted['duration'] = max(int(activity.get('duration', 10) * 0.85), 5)
            adjusted['intensity_adjustment'] = "Decreased"
            adjusted['reps_adjustment'] = "Reduce by 2-3 reps per set"
        else:
            # User doing moderate - maintain
            adjusted['duration'] = activity.get('duration', 10)
            adjusted['intensity_adjustment'] = "Maintained"
            adjusted['reps_adjustment'] = "Keep current reps"
        
        return adjusted

    def should_include_activity(self, activity_engagement_history):
        """
        Decide whether to include/remove activity based on engagement
        
        Args:
            activity_engagement_history: list of engagement scores for specific activity
        
        Returns:
            bool: True if activity should be included, False if should be omitted
        """
        if not activity_engagement_history:
            return True  # Include by default
        
        # Calculate average engagement for this activity
        avg_engagement = sum(activity_engagement_history[-10:]) / len(activity_engagement_history[-10:])
        
        # If average engagement is very low, suggest removal
        if avg_engagement < 0.2 and len(activity_engagement_history) >= 5:
            return False  # Omit this activity
        
        return True  # Include this activity
    
    def recommend_activity_modifications(self, all_activities, engagement_data):
        """
        Recommend which activities to keep/modify/remove based on engagement
        
        Args:
            all_activities: list of activity dicts
            engagement_data: dict mapping activity_name to [engagement scores]
        
        Returns:
            dict: recommendations for activities
        """
        recommendations = {
            'keep': [],
            'increase_difficulty': [],
            'decrease_difficulty': [],
            'remove': []
        }
        
        for activity in all_activities:
            name = activity['name']
            history = engagement_data.get(name, [])
            
            if not self.should_include_activity(history):
                recommendations['remove'].append(name)
            elif history:
                avg_engagement = sum(history[-5:]) / len(history[-5:])
                if avg_engagement > 0.65:
                    recommendations['increase_difficulty'].append(name)
                elif avg_engagement < 0.35:
                    recommendations['decrease_difficulty'].append(name)
                else:
                    recommendations['keep'].append(name)
            else:
                recommendations['keep'].append(name)
        
        return recommendations


class RLModelManager:
    """Handles persistence of RL models (Q-tables)"""
    
    def __init__(self, model_dir='models'):
        """
        Initialize manager with model directory
        
        Args:
            model_dir: directory to store models
        """
        self.model_dir = model_dir
        self.model_path = os.path.join(model_dir, 'wellness_rl_agent.json')
        
        # Create directory if it doesn't exist
        os.makedirs(model_dir, exist_ok=True)

    def save_agent(self, agent):
        """Save agent Q-table and parameters to file"""
        agent_data = {
            'q_table': agent.get_q_table_dict(),
            'epsilon': agent.epsilon,
            'training_history': agent.training_history,
            'hyperparameters': {
                'learning_rate': agent.learning_rate,
                'discount_factor': agent.discount_factor,
                'epsilon_decay': agent.epsilon_decay,
                'min_epsilon': agent.min_epsilon,
                'alpha': agent.alpha,
                'beta': agent.beta,
                'lambda_penalty': agent.lambda_penalty
            }
        }
        
        with open(self.model_path, 'w') as f:
            json.dump(agent_data, f, indent=2)

    def load_agent(self):
        """Load agent from saved file or create new one"""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'r') as f:
                    agent_data = json.load(f)
                
                # Create agent with saved hyperparameters
                hp = agent_data.get('hyperparameters', {})
                agent = WellnessRLAgent(
                    learning_rate=hp.get('learning_rate', 0.1),
                    discount_factor=hp.get('discount_factor', 0.9),
                    initial_epsilon=hp.get('epsilon_decay', 0.995),
                    epsilon_decay=hp.get('epsilon_decay', 0.995),
                    min_epsilon=hp.get('min_epsilon', 0.05)
                )
                
                # Load Q-table and training history
                agent.load_q_table_dict(agent_data.get('q_table', {}))
                agent.epsilon = agent_data.get('epsilon', agent.epsilon)
                agent.training_history = agent_data.get('training_history', agent.training_history)
                
                return agent
            except Exception as e:
                print(f"Error loading agent: {e}. Creating new agent.")
                return WellnessRLAgent()
        else:
            return WellnessRLAgent()
