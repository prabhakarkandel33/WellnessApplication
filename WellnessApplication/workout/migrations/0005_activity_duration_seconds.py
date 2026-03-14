from django.core.validators import MinValueValidator
from django.db import migrations, models


def populate_duration_seconds(apps, schema_editor):
    Activity = apps.get_model('workout', 'Activity')
    for activity in Activity.objects.all().only('id', 'duration_minutes'):
        minutes = activity.duration_minutes or 1
        seconds = max(1, int(minutes) * 60)
        Activity.objects.filter(id=activity.id).update(duration_seconds=seconds)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('workout', '0004_program_completion_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='activity',
            name='duration_seconds',
            field=models.PositiveIntegerField(
                default=600,
                help_text='Exact activity duration in seconds for frontend timer control',
                validators=[MinValueValidator(1)],
            ),
        ),
        migrations.RunPython(populate_duration_seconds, reverse_code=noop_reverse),
    ]
