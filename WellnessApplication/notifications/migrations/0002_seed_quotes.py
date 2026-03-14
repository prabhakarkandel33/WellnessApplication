"""Seed motivational quotes used by the notification rules engine."""
from django.db import migrations


QUOTES = [
    ("The secret of getting ahead is getting started.", "Mark Twain"),
    ("It does not matter how slowly you go as long as you do not stop.", "Confucius"),
    ("Well-being is realized by small steps but is truly no small thing.", "Zeno of Citium"),
    ("Take care of your body. It's the only place you have to live.", "Jim Rohn"),
    ("Health is not about the weight you lose, but about the life you gain.", ""),
    ("Your mental health is a priority. Your happiness is essential. Your self-care is a necessity.", ""),
    ("Exercise is a celebration of what your body can do, not a punishment for what you ate.", ""),
    ("You don't have to be great to start, but you have to start to be great.", "Zig Ziglar"),
    ("The groundwork for all happiness is good health.", "Leigh Hunt"),
    ("Healing is not linear. Every step forward counts.", ""),
    ("Nourish the mind like you would your body. The mind cannot survive on junk food either.", "Jim Rohn"),
    ("Believe you can and you're halfway there.", "Theodore Roosevelt"),
    ("The greatest wealth is health.", "Virgil"),
    ("An apple a day keeps the doctor away, but a grateful heart keeps the blues at bay.", ""),
    ("You are one decision away from a completely different life.", ""),
    ("Movement is medicine for creating change in a person's physical, emotional, and mental states.", ""),
    ("Mindfulness isn't difficult. We just need to remember to do it.", "Sharon Salzberg"),
    ("Rest when you're weary. Refresh and renew yourself, your body, your mind, your spirit.", "Ralph Marston"),
    ("To keep the body in good health is a duty, otherwise we shall not be able to keep our mind strong and clear.", "Buddha"),
    ("Slow progress is still progress.", ""),
]


def seed_quotes(apps, schema_editor):
    MotivationalQuote = apps.get_model('notifications', 'MotivationalQuote')
    for text, author in QUOTES:
        MotivationalQuote.objects.get_or_create(text=text, defaults={'author': author})


def delete_quotes(apps, schema_editor):
    MotivationalQuote = apps.get_model('notifications', 'MotivationalQuote')
    MotivationalQuote.objects.filter(text__in=[t for t, _ in QUOTES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_quotes, reverse_code=delete_quotes),
    ]
