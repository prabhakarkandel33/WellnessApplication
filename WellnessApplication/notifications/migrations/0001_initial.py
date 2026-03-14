import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MotivationalQuote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(unique=True)),
                ('author', models.CharField(blank=True, max_length=150)),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                (
                    'notification_type',
                    models.CharField(
                        choices=[
                            ('motivational_quote', 'Motivational Quote'),
                            ('exercise_reminder', 'Exercise Reminder'),
                            ('weekly_stats', 'Weekly Statistics'),
                            ('journal_reminder', 'Journal Reminder'),
                        ],
                        db_index=True,
                        max_length=30,
                    ),
                ),
                ('title', models.CharField(max_length=200)),
                ('message', models.TextField()),
                ('payload', models.JSONField(blank=True, default=dict, help_text='Extra structured data (e.g. weekly stats dict, quote author).')),
                ('is_read', models.BooleanField(db_index=True, default=False)),
                ('read_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    'user',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='notifications',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['user', 'is_read'], name='notif_user_read_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(
                fields=['user', 'notification_type', 'created_at'],
                name='notif_user_type_created_idx',
            ),
        ),
    ]
