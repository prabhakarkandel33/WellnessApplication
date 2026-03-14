# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workout', '0003_program'),
    ]

    operations = [
        migrations.AddField(
            model_name='program',
            name='completed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='program',
            name='completion_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
