from django.db import migrations


PROMPTS = [
    ('reflection', 'What felt heavier than usual today, and what might it be teaching you?'),
    ('reflection', 'What is one thing you handled better this week than last week?'),
    ('gratitude', 'List three small moments from today that you are genuinely grateful for.'),
    ('gratitude', 'Who made your day easier recently, and how can you acknowledge them?'),
    ('stress', 'Name the top stressor right now. What part of it can you influence today?'),
    ('stress', 'If your stress had a voice, what would it ask you to stop ignoring?'),
    ('goals', 'What is one realistic wellness win you can complete in the next 24 hours?'),
    ('goals', 'Which habit would make the biggest positive change if repeated for 30 days?'),
    ('self_compassion', 'Write one kind sentence to yourself as if you were supporting a friend.'),
    ('self_compassion', 'What went wrong today, and how can you respond with patience instead of criticism?'),
]


def seed_prompts(apps, schema_editor):
    JournalPrompt = apps.get_model('journal', 'JournalPrompt')
    for category, prompt_text in PROMPTS:
        JournalPrompt.objects.get_or_create(
            prompt_text=prompt_text,
            defaults={
                'category': category,
                'is_active': True,
            },
        )


def unseed_prompts(apps, schema_editor):
    JournalPrompt = apps.get_model('journal', 'JournalPrompt')
    prompt_texts = [prompt_text for _, prompt_text in PROMPTS]
    JournalPrompt.objects.filter(prompt_text__in=prompt_texts).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('journal', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_prompts, reverse_code=unseed_prompts),
    ]
