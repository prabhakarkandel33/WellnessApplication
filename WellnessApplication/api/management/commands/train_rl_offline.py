import random
import csv
import os

from django.core.management.base import BaseCommand, CommandError

from api.rl_agent import RLModelManager, WellnessRLAgent


class Command(BaseCommand):
    help = "Offline pretraining for WellnessRLAgent using a simulated user environment."

    def add_arguments(self, parser):
        parser.add_argument(
            "--episodes",
            type=int,
            default=5000,
            help="Number of offline training episodes.",
        )
        parser.add_argument(
            "--steps-per-episode",
            type=int,
            default=1,
            help="State transitions per episode.",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=42,
            help="Random seed for reproducible offline training.",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Start from a fresh agent instead of loading existing model.",
        )
        parser.add_argument(
            "--model-dir",
            type=str,
            default="api/models",
            help="Directory where the RL model JSON is stored.",
        )
        parser.add_argument(
            "--handoff-epsilon",
            type=float,
            default=0.15,
            help=(
                "Exploration rate to set after offline training for online handoff. "
                "Set to -1 to keep the trained epsilon unchanged."
            ),
        )
        parser.add_argument(
            "--no-handoff-reset",
            action="store_true",
            help="Do not override epsilon after offline training.",
        )
        parser.add_argument(
            "--episode-log-path",
            type=str,
            default="api/models/rl_offline_episode_log.csv",
            help=(
                "Output CSV path for episode-level training logs. "
                "Set empty string to disable CSV logging."
            ),
        )
        parser.add_argument(
            "--log-every",
            type=int,
            default=1,
            help="Write one CSV row every N episodes.",
        )

    def handle(self, *args, **options):
        episodes = options["episodes"]
        steps_per_episode = options["steps_per_episode"]
        seed = options["seed"]
        reset = options["reset"]
        model_dir = options["model_dir"]
        handoff_epsilon = options["handoff_epsilon"]
        no_handoff_reset = options["no_handoff_reset"]
        episode_log_path = (options["episode_log_path"] or "").strip()
        log_every = options["log_every"]

        if episodes <= 0:
            raise CommandError("--episodes must be greater than zero.")
        if steps_per_episode <= 0:
            raise CommandError("--steps-per-episode must be greater than zero.")
        if handoff_epsilon != -1 and (handoff_epsilon < 0 or handoff_epsilon > 1):
            raise CommandError("--handoff-epsilon must be between 0 and 1, or -1.")
        if log_every <= 0:
            raise CommandError("--log-every must be greater than zero.")

        rng = random.Random(seed)
        manager = RLModelManager(model_dir=model_dir)
        agent = WellnessRLAgent() if reset else manager.load_agent()

        action_counts = {action_id: 0 for action_id in agent.actions.keys()}
        total_reward = 0.0
        dropout_count = 0
        episode_rows = []
        cumulative_reward = 0.0

        for episode in range(1, episodes + 1):
            state = self._sample_state(rng)
            episode_reward = 0.0
            episode_dropout_count = 0
            episode_action_counts = {action_id: 0 for action_id in agent.actions.keys()}

            for _ in range(steps_per_episode):
                action = int(agent.select_action(state))
                next_state = self._simulate_transition(state, action, rng)
                reward = float(agent.calculate_reward(next_state, action))

                if float(next_state.get("engagement", 0.5)) < 0.1:
                    dropout_count += 1
                    episode_dropout_count += 1

                agent.update_q_value(state, action, reward, next_state)
                state = next_state
                total_reward += reward
                episode_reward += reward
                action_counts[action] = action_counts.get(action, 0) + 1
                episode_action_counts[action] = episode_action_counts.get(action, 0) + 1

            agent.decay_epsilon()

            cumulative_reward += episode_reward
            if episode_log_path and (episode % log_every == 0 or episode == 1 or episode == episodes):
                row = {
                    "episode": episode,
                    "episode_reward_total": round(episode_reward, 6),
                    "episode_reward_avg": round(episode_reward / float(steps_per_episode), 6),
                    "cumulative_reward": round(cumulative_reward, 6),
                    "running_reward_avg": round(cumulative_reward / float(episode * steps_per_episode), 6),
                    "epsilon": round(float(agent.epsilon), 6),
                    "episode_dropouts": episode_dropout_count,
                    "cumulative_dropouts": dropout_count,
                    "q_table_states": len(agent.q_table),
                    "training_episodes": int(agent.training_history.get("episodes", 0)),
                }
                for action_id in sorted(agent.actions.keys()):
                    row[f"action_{action_id}_count"] = int(episode_action_counts.get(action_id, 0))
                episode_rows.append(row)

        epsilon_before_handoff = float(agent.epsilon)
        if (not no_handoff_reset) and handoff_epsilon != -1:
            # Hybrid setup: keep some exploration when switching to live traffic.
            agent.epsilon = max(agent.min_epsilon, float(handoff_epsilon))
            agent.training_history["epsilon_current"] = agent.epsilon

        manager.save_agent(agent)

        total_steps = episodes * steps_per_episode
        average_reward = total_reward / float(total_steps)

        self.stdout.write(self.style.SUCCESS("Offline RL pretraining completed."))
        self.stdout.write(f"Episodes run: {episodes}")
        self.stdout.write(f"Steps per episode: {steps_per_episode}")
        self.stdout.write(f"Total transitions: {total_steps}")
        self.stdout.write(f"Average reward: {average_reward:.4f}")
        self.stdout.write(f"Dropout transitions: {dropout_count}")
        self.stdout.write(f"Epsilon after offline train: {epsilon_before_handoff:.4f}")
        self.stdout.write(f"Epsilon for online handoff: {agent.epsilon:.4f}")
        self.stdout.write(f"Training history episodes: {agent.training_history['episodes']}")
        self.stdout.write("Action counts:")
        for action_id in sorted(action_counts.keys()):
            self.stdout.write(f"  {action_id} ({agent.get_action_name(action_id)}): {action_counts[action_id]}")

        if episode_log_path:
            self._write_episode_log(episode_log_path, episode_rows)
            self.stdout.write(f"Episode CSV log written to: {episode_log_path}")

    def _sample_state(self, rng):
        """Generate a plausible user state in the encoded RL feature space."""
        stress = rng.randint(0, 2)
        mental = rng.randint(0, 4)
        exercise_level = rng.randint(0, 2)

        base_engagement = 0.55 - (0.08 * stress) - (0.04 * max(0, mental - 1)) + (0.06 * exercise_level)
        base_engagement += rng.uniform(-0.08, 0.08)

        return {
            "age": rng.randint(18, 65),
            "gender": rng.randint(0, 1),
            "diet_type": rng.randint(0, 4),
            "exercise_level": exercise_level,
            "stress_level": stress,
            "mental_health_condition": mental,
            "sleep_hours": rng.uniform(4.5, 8.5),
            "work_hours_per_week": rng.uniform(25, 65),
            "screen_time_per_day": rng.uniform(3.0, 12.0),
            "social_interaction_score": rng.randint(1, 9),
            "happiness_score": rng.randint(2, 8),
            "engagement": self._clamp(base_engagement, 0.0, 1.0),
            "motivation": rng.randint(1, 5),
            "segment": rng.randint(0, 4),
        }

    def _simulate_transition(self, state, action, rng):
        """Simple environment model that maps action choice to next state quality."""
        next_state = dict(state)

        stress = int(next_state.get("stress_level", 1))
        mental = int(next_state.get("mental_health_condition", 0))

        # Action effects on engagement and motivation.
        effects = {
            0: (0.05, 0.10),   # Increase Workout Intensity
            1: (0.02, 0.08),   # Decrease Workout Intensity
            2: (0.03, 0.12),   # Increase Meditation Frequency
            3: (0.01, 0.09),   # Send Motivational Message
            4: (0.02, 0.10),   # Increase Mental Recovery Focus
            5: (0.01, 0.04),   # Maintain Current Plan
        }
        base_eng_delta, base_mot_delta = effects.get(int(action), (0.0, 0.0))

        # Contextual suitability for action selection.
        if action == 0 and stress >= 2:
            base_eng_delta -= 0.06
            base_mot_delta -= 0.08
        if action == 1 and state.get("exercise_level", 1) <= 0:
            base_eng_delta -= 0.03
        if action == 2 and (stress >= 1 or mental in (2, 3, 4)):
            base_eng_delta += 0.04
            base_mot_delta += 0.05
        if action == 4 and (mental in (2, 3, 4)):
            base_eng_delta += 0.03
            base_mot_delta += 0.04

        noise_eng = rng.uniform(-0.06, 0.06)
        noise_mot = rng.uniform(-0.25, 0.25)

        current_eng = float(state.get("engagement", 0.5))
        current_mot = int(state.get("motivation", 3))

        next_engagement = self._clamp(current_eng + base_eng_delta + noise_eng, 0.0, 1.0)
        next_motivation = int(round(self._clamp(current_mot + base_mot_delta + noise_mot, 1.0, 5.0)))

        # Dropout risk modeled as a probabilistic collapse in engagement.
        dropout_risk = 0.02
        dropout_risk += 0.10 if current_eng < 0.25 else 0.0
        dropout_risk += 0.06 if current_mot <= 2 else 0.0
        dropout_risk += 0.05 if stress >= 2 else 0.0
        dropout_risk += 0.03 if mental in (2, 3, 4) else 0.0

        if action == 2:
            dropout_risk -= 0.03
        if action == 3:
            dropout_risk -= 0.02
        if action == 4:
            dropout_risk -= 0.03

        dropout_risk = self._clamp(dropout_risk, 0.0, 0.5)
        if rng.random() < dropout_risk:
            next_engagement = min(next_engagement, rng.uniform(0.0, 0.09))
            next_motivation = min(next_motivation, 2)

        # Co-evolve a few state indicators to avoid static transitions.
        next_state["engagement"] = next_engagement
        next_state["motivation"] = next_motivation
        next_state["happiness_score"] = int(round(self._clamp(
            int(state.get("happiness_score", 5)) + (next_motivation - current_mot),
            0,
            10,
        )))

        sleep = float(state.get("sleep_hours", 7.0))
        next_state["sleep_hours"] = self._clamp(sleep + rng.uniform(-0.4, 0.4), 0.0, 9.0)

        screen = float(state.get("screen_time_per_day", 6.0))
        screen_shift = -0.4 if next_engagement > current_eng else 0.2
        next_state["screen_time_per_day"] = self._clamp(screen + screen_shift + rng.uniform(-0.3, 0.3), 0.0, 24.0)

        return next_state

    def _clamp(self, value, lower, upper):
        return max(lower, min(upper, value))

    def _write_episode_log(self, path, rows):
        """Persist episode-level logs to CSV for learning-curve plots."""
        if not rows:
            return

        output_dir = os.path.dirname(path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        fieldnames = list(rows[0].keys())
        with open(path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
