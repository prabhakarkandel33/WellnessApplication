from rest_framework import serializers

from notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    notification_type_display = serializers.SerializerMethodField()

    class Meta:
        model  = Notification
        fields = [
            'id',
            'notification_type',
            'notification_type_display',
            'title',
            'message',
            'payload',
            'is_read',
            'read_at',
            'created_at',
        ]
        read_only_fields = fields

    def get_notification_type_display(self, obj):
        return obj.get_notification_type_display()


class MotivationalQuotePayloadSerializer(serializers.Serializer):
    quote = serializers.CharField(help_text='Motivational quote text.')
    author = serializers.CharField(
        allow_blank=True,
        help_text='Optional quote author.',
    )


class ExerciseReminderPayloadSerializer(serializers.Serializer):
    date = serializers.DateField(
        help_text='Date for which no completed exercise was detected.',
    )


class WeeklyStatsPayloadSerializer(serializers.Serializer):
    week = serializers.CharField(help_text='ISO week identifier, e.g. 2026-W11.')
    total_activities = serializers.IntegerField()
    exercises = serializers.IntegerField()
    meditations = serializers.IntegerField()
    journaling = serializers.IntegerField()
    total_minutes = serializers.IntegerField()
    avg_motivation_after = serializers.FloatField(allow_null=True)


class JournalReminderPayloadSerializer(serializers.Serializer):
    last_entry_check = serializers.DateField(
        help_text='Cutoff date used to detect journal inactivity.',
    )


class NotificationSchemaBaseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    notification_type = serializers.ChoiceField(choices=Notification.Type.choices)
    notification_type_display = serializers.CharField()
    title = serializers.CharField()
    message = serializers.CharField()
    is_read = serializers.BooleanField()
    read_at = serializers.DateTimeField(allow_null=True)
    created_at = serializers.DateTimeField()


class MotivationalQuoteNotificationSchemaSerializer(NotificationSchemaBaseSerializer):
    payload = MotivationalQuotePayloadSerializer()


class ExerciseReminderNotificationSchemaSerializer(NotificationSchemaBaseSerializer):
    payload = ExerciseReminderPayloadSerializer()


class WeeklyStatsNotificationSchemaSerializer(NotificationSchemaBaseSerializer):
    payload = WeeklyStatsPayloadSerializer()


class JournalReminderNotificationSchemaSerializer(NotificationSchemaBaseSerializer):
    payload = JournalReminderPayloadSerializer()


class MarkReadRequestSerializer(serializers.Serializer):
    ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
        help_text='List of notification IDs to mark as read.',
    )


class MarkReadResponseSerializer(serializers.Serializer):
    marked_read = serializers.IntegerField(help_text='Number of notifications updated.')


class GenerateNotificationsResponseSerializer(serializers.Serializer):
    generated = serializers.IntegerField(help_text='Total new notifications created.')
    breakdown = serializers.DictField(
        child=serializers.IntegerField(),
        help_text='Count per notification type.',
    )
