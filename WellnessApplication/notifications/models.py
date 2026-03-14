from django.conf import settings
from django.db import models
from django.utils import timezone


class Notification(models.Model):
    """
    Persisted notification record for a user.
    The client polls GET /api/notifications/ to fetch unread items.
    """

    class Type(models.TextChoices):
        MOTIVATIONAL_QUOTE   = 'motivational_quote',   'Motivational Quote'      # every 48 h
        EXERCISE_REMINDER    = 'exercise_reminder',    'Exercise Reminder'       # no exercise today
        WEEKLY_STATS         = 'weekly_stats',         'Weekly Statistics'       # end of week summary
        JOURNAL_REMINDER     = 'journal_reminder',     'Journal Reminder'        # no entry in 3 days

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    notification_type = models.CharField(max_length=30, choices=Type.choices, db_index=True)
    title   = models.CharField(max_length=200)
    message = models.TextField()
    payload = models.JSONField(default=dict, blank=True,
        help_text='Extra structured data (e.g. weekly stats dict, quote author).')

    is_read     = models.BooleanField(default=False, db_index=True)
    read_at     = models.DateTimeField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read'], name='notif_user_read_idx'),
            models.Index(
                fields=['user', 'notification_type', 'created_at'],
                name='notif_user_type_created_idx',
            ),
        ]

    def __str__(self):
        return f'[{self.notification_type}] {self.user.username} – {self.title}'

    def mark_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class MotivationalQuote(models.Model):
    text   = models.TextField(unique=True)
    author = models.CharField(max_length=150, blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'"{self.text[:60]}" — {self.author or "Unknown"}'
