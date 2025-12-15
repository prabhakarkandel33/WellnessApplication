from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_alter_customuser_gad7_score_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='engagement_score',
            field=models.FloatField(default=0.5, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1)], help_text='User engagement score (0-1) for RL agent'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='motivation_score',
            field=models.PositiveIntegerField(default=3, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)], help_text='User motivation score (1-5) for RL agent'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='workouts_completed',
            field=models.PositiveIntegerField(default=0, help_text='Total number of workouts completed'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='meditation_sessions',
            field=models.PositiveIntegerField(default=0, help_text='Total number of meditation sessions completed'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='last_action_recommended',
            field=models.PositiveIntegerField(default=5, null=True, blank=True, help_text='Last RL action recommended (0-5)'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='last_recommendation_date',
            field=models.DateTimeField(auto_now=False, null=True, blank=True, help_text='When the last RL recommendation was made'),
        ),
    ]
