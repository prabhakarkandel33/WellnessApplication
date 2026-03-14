from django.db import migrations


CBT_PROMPTS = [
    ('thought_record', 'Describe the situation: where were you, what were you doing, and who was with you when the upsetting feeling started?'),
    ('thought_record', 'What automatic thought went through your mind in that moment? Write it exactly as it appeared.'),
    ('thought_record', 'What emotion(s) did you feel and how intense were they on a scale of 0 to 100?'),
    ('thought_record', 'What evidence do you have that supports this automatic thought as being true?'),
    ('thought_record', 'What evidence contradicts or challenges this automatic thought?'),
    ('thought_record', 'If a close friend told you they had this thought in this situation, what would you say to them?'),
    ('thought_record', 'Write a balanced, alternative thought that takes both the evidence for and against into account.'),
    ('thought_record', 'After writing your balanced thought, how intense are those emotions now on a scale of 0 to 100?'),
    ('thought_record', 'What is one small action you can take today based on this more balanced perspective?'),
    ('thought_record', 'Which thinking patterns did you notice — all-or-nothing thinking, catastrophizing, mind reading, or something else?'),
    ('stress', 'Write down the worst realistic outcome of this stressor, then write what you would do if that actually happened.'),
    ('self_compassion', 'What would you say to yourself if you spoke to yourself with the same kindness you show a good friend in this situation?'),
    ('reflection', 'Looking back at an entry you wrote a week or more ago — has your perspective changed? What would you add now?'),
    ('gratitude', 'Write about a difficult moment today that also contained something you can be grateful for, even if it is small.'),
    ('goals', 'Identify one belief about yourself that might be holding you back from a goal. Where do you think that belief came from?'),
]


def seed_cbt_prompts(apps, schema_editor):
    JournalPrompt = apps.get_model('journal', 'JournalPrompt')
    for category, prompt_text in CBT_PROMPTS:
        JournalPrompt.objects.get_or_create(
            prompt_text=prompt_text,
            defaults={
                'category': category,
                'is_active': True,
            },
        )


def unseed_cbt_prompts(apps, schema_editor):
    JournalPrompt = apps.get_model('journal', 'JournalPrompt')
    JournalPrompt.objects.filter(prompt_text__in=[p for _, p in CBT_PROMPTS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('journal', '0003_cbt_fields'),
    ]

    operations = [
        migrations.RunPython(seed_cbt_prompts, reverse_code=unseed_cbt_prompts),
    ]
