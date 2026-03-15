import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Avg
from django.utils import timezone

from api.signals import _update_user_statistics
from workout.activities import ACTIVITIES_BY_SEGMENT
from workout.models import Activity, WorkoutSession

SEED_MARKER = "[startup-stats-seed]"


class Command(BaseCommand):
    help = "Flood every user with seeded activity/session history and refresh statistics."

    def add_arguments(self, parser):
        parser.add_argument(
            "--activities-per-user",
            type=int,
            default=24,
            help="How many historical activities to create per user.",
        )
        parser.add_argument(
            "--days-back",
            type=int,
            default=45,
            help="How many days back to spread generated activity history.",
        )
        parser.add_argument(
            "--completion-rate",
            type=float,
            default=0.82,
            help="Completion ratio for generated activities (0.0 to 1.0).",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Delete previous startup seeded statistics data and regenerate.",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=None,
            help="Optional random seed for reproducible generated data.",
        )

    def handle(self, *args, **options):
        activities_per_user = options["activities_per_user"]
        days_back = options["days_back"]
        completion_rate = options["completion_rate"]
        force = options["force"]
        base_seed = options["seed"]

        if activities_per_user <= 0:
            raise CommandError("--activities-per-user must be greater than zero.")
        if days_back <= 0:
            raise CommandError("--days-back must be greater than zero.")
        if completion_rate < 0 or completion_rate > 1:
            raise CommandError("--completion-rate must be between 0.0 and 1.0.")

        user_model = get_user_model()
        users = list(user_model.objects.all())
        if not users:
            self.stdout.write("No users found. Nothing to seed.")
            return

        templates = _build_activity_templates()

        users_seeded = 0
        users_skipped = 0
        activities_created = 0
        sessions_created = 0

        for user in users:
            rng = random.Random()
            if base_seed is not None:
                rng = random.Random(f"{base_seed}:{user.pk}")

            already_seeded = Activity.objects.filter(
                user=user,
                notes__icontains=SEED_MARKER,
            ).exists()

            if already_seeded and not force:
                users_skipped += 1
                self._refresh_rollups(user)
                continue

            with transaction.atomic():
                if force:
                    WorkoutSession.objects.filter(
                        user=user,
                        session_notes__icontains=SEED_MARKER,
                    ).delete()
                    Activity.objects.filter(
                        user=user,
                        notes__icontains=SEED_MARKER,
                    ).delete()

                created_count, created_sessions = self._seed_for_user(
                    user=user,
                    rng=rng,
                    templates=templates,
                    activities_per_user=activities_per_user,
                    days_back=days_back,
                    completion_rate=completion_rate,
                )
                self._refresh_rollups(user)

                users_seeded += 1
                activities_created += created_count
                sessions_created += created_sessions

        self.stdout.write(
            self.style.SUCCESS(
                "Statistics flood complete. "
                f"Users seeded: {users_seeded}. "
                f"Users skipped (already seeded): {users_skipped}. "
                f"Activities created: {activities_created}. "
                f"Sessions created: {sessions_created}."
            )
        )

    def _seed_for_user(self, user, rng, templates, activities_per_user, days_back, completion_rate):
        now = timezone.now()
        created_activity_ids = []

        for _ in range(activities_per_user):
            template = rng.choice(templates)
            day_offset = rng.randint(0, days_back - 1)
            minute_offset = rng.randint(0, (23 * 60) + 59)
            assigned_at = now - timedelta(days=day_offset, minutes=minute_offset)

            completed = rng.random() <= completion_rate
            completion_at = None
            motivation_before = None
            motivation_after = None
            difficulty_rating = None
            enjoyment_rating = None

            if completed:
                motivation_before = rng.randint(1, 4)
                delta = rng.choice([-1, 0, 1, 1, 2])
                motivation_after = max(1, min(5, motivation_before + delta))
                difficulty_rating = rng.randint(2, 5)
                enjoyment_rating = rng.randint(2, 5)
                completion_at = assigned_at + timedelta(
                    minutes=max(1, int(template["duration_minutes"])) + rng.randint(0, 20)
                )

            activity = Activity.objects.create(
                user=user,
                activity_name=template["name"],
                activity_type=template["type"],
                description=template["description"],
                duration_minutes=template["duration_minutes"],
                duration_seconds=template["duration_minutes"] * 60,
                intensity=template["intensity"],
                instructions=template["instructions"],
                assigned_date=assigned_at,
                completion_date=completion_at,
                completed=completed,
                motivation_before=motivation_before,
                motivation_after=motivation_after,
                difficulty_rating=difficulty_rating,
                enjoyment_rating=enjoyment_rating,
                notes=(
                    f"{SEED_MARKER} "
                    f"generated_at={now.isoformat()} "
                    f"template={template['name']}"
                ),
            )

            Activity.objects.filter(pk=activity.pk).update(
                created_at=assigned_at,
                updated_at=completion_at or assigned_at,
            )
            created_activity_ids.append(activity.pk)

        created_sessions = self._create_seeded_sessions(
            user=user,
            activity_ids=created_activity_ids,
            rng=rng,
            now=now,
        )

        return len(created_activity_ids), created_sessions

    def _create_seeded_sessions(self, user, activity_ids, rng, now):
        activities = list(
            Activity.objects.filter(pk__in=activity_ids).order_by("assigned_date")
        )
        if not activities:
            return 0

        chunk_size = 4
        created_sessions = 0

        for offset in range(0, len(activities), chunk_size):
            chunk = activities[offset : offset + chunk_size]
            if not chunk:
                continue

            completed_times = [a.completion_date for a in chunk if a.completion_date]
            session_start = min((a.assigned_date or now) for a in chunk)
            session_end = max(completed_times) if completed_times else None

            session = WorkoutSession.objects.create(
                user=user,
                session_type="daily",
                completed_at=session_end,
                overall_session_rating=rng.randint(3, 5) if session_end else None,
                session_notes=f"{SEED_MARKER} generated_at={now.isoformat()}",
            )
            session.activities.set(chunk)
            session.calculate_metrics()
            WorkoutSession.objects.filter(pk=session.pk).update(created_at=session_start)
            created_sessions += 1

        return created_sessions

    def _refresh_rollups(self, user):
        user_activities = Activity.objects.filter(user=user)
        completed_activities = user_activities.filter(completed=True)

        total_activities = user_activities.count()
        completed_count = completed_activities.count()

        user.workouts_completed = WorkoutSession.objects.filter(
            user=user,
            completion_rate__gt=0,
        ).count()
        user.meditation_sessions = completed_activities.filter(
            activity_type="meditation"
        ).count()

        motivation_after_avg = completed_activities.exclude(
            motivation_after__isnull=True
        ).aggregate(avg=Avg("motivation_after"))["avg"]
        if motivation_after_avg is not None:
            user.motivation_score = max(1, min(5, int(round(motivation_after_avg))))

        user.engagement_score = (
            round(completed_count / total_activities, 2) if total_activities else 0.0
        )

        user.save(
            update_fields=[
                "workouts_completed",
                "meditation_sessions",
                "motivation_score",
                "engagement_score",
            ]
        )

        _update_user_statistics(user)


def _build_activity_templates():
    templates = []

    for segment_data in ACTIVITIES_BY_SEGMENT.values():
        for bucket in ("physical", "mental"):
            for candidate in segment_data.get(bucket, []):
                activity_type = candidate.get("type")
                if activity_type not in {"exercise", "meditation"}:
                    continue

                templates.append(
                    {
                        "name": candidate.get("name", "Wellness Activity"),
                        "type": activity_type,
                        "duration_minutes": max(1, int(candidate.get("duration", 10))),
                        "intensity": candidate.get("intensity", "Moderate"),
                        "description": candidate.get(
                            "description", "Generated startup activity for statistics."
                        ),
                        "instructions": candidate.get("instructions", []),
                    }
                )

    if templates:
        return templates

    return [
        {
            "name": "Brisk Walk",
            "type": "exercise",
            "duration_minutes": 20,
            "intensity": "Moderate",
            "description": "Generated fallback workout.",
            "instructions": ["Walk at a steady pace for 20 minutes."],
        },
        {
            "name": "Breathing Session",
            "type": "meditation",
            "duration_minutes": 10,
            "intensity": "Low",
            "description": "Generated fallback mindfulness session.",
            "instructions": ["Focus on slow breaths for 10 minutes."],
        },
    ]
