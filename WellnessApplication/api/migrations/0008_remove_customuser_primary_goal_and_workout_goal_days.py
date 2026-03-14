# Generated manually

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_alter_customuser_gender'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='primary_goal',
        ),
        migrations.RemoveField(
            model_name='customuser',
            name='workout_goal_days',
        ),
    ]
