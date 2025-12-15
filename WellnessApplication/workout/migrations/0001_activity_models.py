# Generated migration for Activity and WorkoutSession models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('activity_name', models.CharField(max_length=255)),
                ('activity_type', models.CharField(choices=[('exercise', 'Exercise'), ('meditation', 'Meditation'), ('journaling', 'Journaling')], max_length=50)),
                ('duration_minutes', models.IntegerField()),
                ('intensity', models.CharField(choices=[('Low', 'Low'), ('Moderate', 'Moderate'), ('High', 'High')], max_length=50)),
                ('description', models.TextField()),
                ('instructions', models.JSONField(default=list)),
                ('motivation_before', models.IntegerField(choices=[(1, '1 - Not Motivated'), (2, '2 - Slightly Motivated'), (3, '3 - Neutral'), (4, '4 - Motivated'), (5, '5 - Very Motivated')], null=True, blank=True)),
                ('motivation_after', models.IntegerField(choices=[(1, '1 - Not Motivated'), (2, '2 - Slightly Motivated'), (3, '3 - Neutral'), (4, '4 - Motivated'), (5, '5 - Very Motivated')], null=True, blank=True)),
                ('difficulty_rating', models.IntegerField(choices=[(1, '1 - Too Easy'), (2, '2 - Easy'), (3, '3 - Just Right'), (4, '4 - Challenging'), (5, '5 - Too Hard')], null=True, blank=True)),
                ('enjoyment_rating', models.IntegerField(choices=[(1, '1 - Disliked'), (2, '2 - Somewhat Disliked'), (3, '3 - Neutral'), (4, '4 - Enjoyed'), (5, '5 - Loved It')], null=True, blank=True)),
                ('completed', models.BooleanField(default=False)),
                ('completion_date', models.DateTimeField(null=True, blank=True)),
                ('notes', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='WorkoutSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_date', models.DateTimeField(auto_now_add=True)),
                ('overall_rating', models.IntegerField(choices=[(1, '1 - Poor'), (2, '2 - Fair'), (3, '3 - Good'), (4, '4 - Very Good'), (5, '5 - Excellent')], default=3)),
                ('notes', models.TextField(blank=True, default='')),
                ('completion_rate', models.FloatField(default=0, help_text='Percentage of activities completed')),
                ('avg_motivation_before', models.FloatField(default=0)),
                ('avg_motivation_after', models.FloatField(default=0)),
                ('avg_motivation_delta', models.FloatField(default=0)),
                ('avg_difficulty_rating', models.FloatField(default=0)),
                ('avg_enjoyment_rating', models.FloatField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('activities', models.ManyToManyField(related_name='sessions', to='workout.Activity')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-session_date'],
            },
        ),
    ]
