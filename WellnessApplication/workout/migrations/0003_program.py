# Generated manually

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workout', '0002_alter_activity_options_alter_workoutsession_options_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Program',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('program_type', models.CharField(
                    choices=[('physical', 'Physical'), ('mental', 'Mental')],
                    max_length=10,
                )),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('segment', models.CharField(blank=True, max_length=100)),
                ('duration', models.CharField(blank=True, max_length=100)),
                ('frequency', models.CharField(blank=True, max_length=100)),
                ('intensity', models.CharField(blank=True, max_length=50)),
                ('progression', models.TextField(blank=True)),
                ('focus', models.CharField(blank=True, max_length=200)),
                ('rl_action_id', models.IntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='programs',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddField(
            model_name='activity',
            name='program',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='activities',
                to='workout.program',
            ),
        ),
        migrations.AlterField(
            model_name='activity',
            name='activity_type',
            field=models.CharField(
                choices=[('exercise', 'Exercise'), ('meditation', 'Meditation')],
                max_length=20,
            ),
        ),
    ]
