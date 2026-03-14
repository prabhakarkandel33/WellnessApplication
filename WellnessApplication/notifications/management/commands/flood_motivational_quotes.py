from django.core.management.base import BaseCommand

from notifications.models import MotivationalQuote
from notifications.quote_catalog import MOTIVATIONAL_QUOTES


class Command(BaseCommand):
    help = 'Flood the database with a large catalog of motivational quotes.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=200,
            help='Batch size used for bulk insertion.',
        )

    def handle(self, *args, **options):
        existing_texts = set(MotivationalQuote.objects.values_list('text', flat=True))
        to_create = [
            MotivationalQuote(text=text, author=author)
            for text, author in MOTIVATIONAL_QUOTES
            if text not in existing_texts
        ]

        if to_create:
            MotivationalQuote.objects.bulk_create(
                to_create,
                batch_size=options['batch_size'],
            )

        total = MotivationalQuote.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f'Motivational quotes ready. Added {len(to_create)} new quotes. '
                f'Total available quotes: {total}.'
            )
        )