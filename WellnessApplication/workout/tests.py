from django.test import SimpleTestCase
from django.contrib.auth import get_user_model
from django.test import override_settings
from unittest.mock import MagicMock

from rest_framework import status
from rest_framework.test import APITestCase

from workout.views import RecommendedActivitiesView
from workout.views import ActivityFeedbackBatchView
from workout.models import Program, Activity, WorkoutSession


class ActivityExpansionTests(SimpleTestCase):
	def setUp(self):
		# Helper methods under test do not depend on request context.
		self.view = RecommendedActivitiesView.__new__(RecommendedActivitiesView)

	def test_exercise_circuit_splits_into_atomic_movements(self):
		item = {
			"name": "Bodyweight Circuit: 15 Minutes",
			"type": "exercise",
			"duration": 15,
			"intensity": "Moderate",
			"description": "Compound movements using body weight for strength and cardio",
			"instructions": [
				"SET 1 (Repeat 3 times):",
				"1. Push-ups: 8-10 repetitions (on knees or incline if needed)",
				"2. Bodyweight squats: 15 repetitions",
				"3. Plank: Hold for 30 seconds",
				"4. Rest for 60 seconds between sets",
				"Tips:",
				"- For push-ups: hands shoulder-width, lower until elbows bend to 90 degrees",
			],
		}

		units = self.view._expand_catalog_activity(item)
		names = [unit["activity_name"] for unit in units]

		self.assertEqual(len(units), 12)
		self.assertEqual(len([name for name in names if "Push-ups" in name]), 3)
		self.assertEqual(len([name for name in names if "Bodyweight squats" in name]), 3)
		self.assertEqual(len([name for name in names if "Plank" in name]), 3)
		self.assertEqual(len([name for name in names if "Rest" in name]), 3)

		plank_unit = next(unit for unit in units if "Plank" in unit["activity_name"])
		rest_unit = next(unit for unit in units if "Rest" in unit["activity_name"])
		pushups_unit = next(unit for unit in units if "Push-ups" in unit["activity_name"])

		self.assertEqual(plank_unit["duration_seconds"], 30)
		self.assertEqual(rest_unit["duration_seconds"], 60)
		self.assertGreaterEqual(pushups_unit["duration_seconds"], 20)

		# Verify circuit ordering is round-based: all movements in round 1 before round 2.
		self.assertIn("Push-ups (Round 1)", units[0]["activity_name"])
		self.assertIn("Bodyweight squats (Round 1)", units[1]["activity_name"])
		self.assertIn("Plank (Round 1)", units[2]["activity_name"])
		self.assertIn("Rest (Round 1)", units[3]["activity_name"])
		self.assertIn("Push-ups (Round 2)", units[4]["activity_name"])

	def test_non_split_activity_falls_back_to_single_row(self):
		item = {
			"name": "Brisk Walking: 20 Minutes",
			"type": "exercise",
			"duration": 20,
			"intensity": "Moderate",
			"description": "Faster-paced walking that elevates heart rate",
			"instructions": [
				"1. Warm up with 2 minutes of slow walking",
				"2. Increase pace to brisk",
				"3. Maintain good posture",
				"4. Cool down with 3 minutes of slow walking",
			],
		}

		units = self.view._expand_catalog_activity(item)

		self.assertEqual(len(units), 1)
		self.assertEqual(units[0]["activity_name"], "Brisk Walking")
		self.assertEqual(units[0]["duration_seconds"], 1200)

	def test_leading_duration_prefix_is_removed_from_name(self):
		item = {
			"name": "5-Min Gentle Stretching",
			"type": "exercise",
			"duration": 5,
			"intensity": "Low",
			"description": "Gentle stretching to release tension",
			"instructions": [
				"1. Neck rolls",
				"2. Shoulder shrugs",
			],
		}

		units = self.view._expand_catalog_activity(item)

		self.assertEqual(len(units), 1)
		self.assertEqual(units[0]["activity_name"], "Gentle Stretching")


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
class ActivityCompletionEndpointTests(APITestCase):
	def setUp(self):
		user_model = get_user_model()
		self.user = user_model.objects.create_user(
			username="activity-completion-user",
			email="activity-completion@example.com",
			password="testpass123",
		)

		self.program = Program.objects.create(
			user=self.user,
			program_type=Program.ProgramType.PHYSICAL,
			name="Completion Program",
			description="Completion endpoint test",
			duration="20 minutes",
			frequency="Daily",
			intensity="Moderate",
		)

		self.activity = Activity.objects.create(
			user=self.user,
			program=self.program,
			activity_name="Brisk Walking",
			activity_type="exercise",
			description="Walking set",
			duration_minutes=5,
			duration_seconds=300,
			intensity="Moderate",
			instructions=["Walk briskly"],
		)

		self.client.force_authenticate(user=self.user)

	def test_complete_activity_without_motivation(self):
		response = self.client.post(
			f"/api/workout/activity/{self.activity.id}/complete/",
			{"completed": True},
			format="json",
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK, getattr(response, "data", None))
		self.activity.refresh_from_db()
		self.assertTrue(self.activity.completed)
		self.assertIsNone(self.activity.motivation_after)
		self.assertEqual(response.data.get("motivation"), None)


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
class RecommendationPrivacyEndpointTests(APITestCase):
	def setUp(self):
		user_model = get_user_model()
		self.user = user_model.objects.create_user(
			username="recommendation-privacy-user",
			email="recommendation-privacy@example.com",
			password="testpass123",
		)

		mock_agent = MagicMock()
		mock_agent.select_action.return_value = 5
		mock_agent.adjust_activity_difficulty.side_effect = lambda activity, *_: activity
		RecommendedActivitiesView.rl_agent = mock_agent

		self.client.force_authenticate(user=self.user)

	def test_recommendation_response_hides_rl_policy_fields(self):
		response = self.client.get("/api/workout/activity/recommended/")

		self.assertEqual(response.status_code, status.HTTP_200_OK, getattr(response, "data", None))
		self.assertIn("recommendation_note", response.data)
		self.assertNotIn("rl_action", response.data)
		self.assertNotIn("rl_action_name", response.data)
		self.assertNotIn("reason", response.data)

		self.assertNotIn("rl_action_id", response.data["physical_program"])
		self.assertNotIn("rl_action_id", response.data["mental_program"])

		for activity in response.data["physical_program"].get("activities", []):
			self.assertNotIn("rl_action_id", activity)
		for activity in response.data["mental_program"].get("activities", []):
			self.assertNotIn("rl_action_id", activity)


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
class ProgramFeedbackEndpointTests(APITestCase):
	def setUp(self):
		user_model = get_user_model()
		self.user = user_model.objects.create_user(
			username="program-feedback-user",
			email="program-feedback@example.com",
			password="testpass123",
		)

		self.program = Program.objects.create(
			user=self.user,
			program_type=Program.ProgramType.PHYSICAL,
			name="Atomic Program",
			description="Program-level feedback test",
			duration="20 minutes",
			frequency="Daily",
			intensity="Moderate",
		)

		self.activity_a = Activity.objects.create(
			user=self.user,
			program=self.program,
			activity_name="Push-ups",
			activity_type="exercise",
			description="Push-up set",
			duration_minutes=5,
			duration_seconds=300,
			intensity="Moderate",
			instructions=["Do push-ups"],
		)
		self.activity_b = Activity.objects.create(
			user=self.user,
			program=self.program,
			activity_name="Sit-ups",
			activity_type="exercise",
			description="Sit-up set",
			duration_minutes=5,
			duration_seconds=300,
			intensity="Moderate",
			instructions=["Do sit-ups"],
		)

		ActivityFeedbackBatchView.rl_agent = MagicMock()
		ActivityFeedbackBatchView.rl_agent.epsilon = 0.2
		ActivityFeedbackBatchView.rl_agent.training_history = {
			"episodes": 10,
			"total_reward": 5.5,
		}
		ActivityFeedbackBatchView.rl_agent.recommend_activity_modifications.return_value = []
		ActivityFeedbackBatchView.rl_model_manager = MagicMock()

		self.client.force_authenticate(user=self.user)

	def test_program_feedback_applies_to_all_program_activities(self):
		response = self.client.post(
			f"/api/workout/programs/{self.program.id}/feedback/",
			{
				"completed": True,
				"motivation": 4,
				"overall_session_rating": 5,
				"notes": "Whole program done",
			},
			format="json",
		)

		self.assertEqual(response.status_code, status.HTTP_201_CREATED, getattr(response, "data", None))
		self.assertEqual(response.data["session"]["activities_count"], 2)
		self.assertEqual(response.data["session"]["completed_activities"], 2)

		self.activity_a.refresh_from_db()
		self.activity_b.refresh_from_db()
		self.program.refresh_from_db()

		self.assertTrue(self.activity_a.completed)
		self.assertTrue(self.activity_b.completed)
		self.assertEqual(self.activity_a.motivation_after, 4)
		self.assertEqual(self.activity_b.motivation_after, 4)
		self.assertTrue(self.program.completed)

		self.assertEqual(WorkoutSession.objects.filter(user=self.user).count(), 1)
		self.assertTrue(ActivityFeedbackBatchView.rl_agent.update_q_value.called)
		self.assertTrue(ActivityFeedbackBatchView.rl_model_manager.save_agent.called)
