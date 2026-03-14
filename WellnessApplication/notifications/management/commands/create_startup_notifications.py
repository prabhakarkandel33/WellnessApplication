import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from notifications.models import MotivationalQuote, Notification


class Command(BaseCommand):
    help = (
        "Create startup notifications for every user: "
        "one motivational quote and one workout reminder."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch-size",
            type=int,
            default=500,
            help="Batch size used for bulk insertion.",
        )

    def handle(self, *args, **options):
        user_model = get_user_model()
        users = list(user_model.objects.all())

        if not users:
            self.stdout.write("No users found. No startup notifications created.")
            return

        quotes = list(MotivationalQuote.objects.values_list("text", "author"))
        fallback_quote = (
            "Small steps every day lead to big changes over time.",
            "",
        )

        today = timezone.localdate().isoformat()
        to_create = []

        for user in users:
            quote_text, quote_author = random.choice(quotes) if quotes else fallback_quote
            quote_message = f'"{quote_text}"' + (f" - {quote_author}" if quote_author else "")

            to_create.append(
                Notification(
                    user=user,
                    notification_type=Notification.Type.MOTIVATIONAL_QUOTE,
                    title="Your startup motivation",
                    message=quote_message,
                    payload={
                        "quote": quote_text,
                        "author": quote_author,
                        "startup_seeded": True,
                    },
                )
            )

            to_create.append(
                Notification(
                    user=user,
                    notification_type=Notification.Type.EXERCISE_REMINDER,
                    title="No workout logged yet",
                    message=(
                        "You have not completed a workout yet. "
                        "Open your recommended activities and finish one today."
                    ),
                    payload={
                        "date": today,
                        "startup_seeded": True,
                    },
                )
            )

        Notification.objects.bulk_create(
            to_create,
            batch_size=options["batch_size"],
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Startup notifications created. "
                f"Users processed: {len(users)}. "
                f"Notifications created: {len(to_create)}."
            )
        )
