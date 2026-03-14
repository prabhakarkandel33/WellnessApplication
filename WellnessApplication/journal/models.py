from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class JournalTag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)[:55] or 'tag'
            candidate = base_slug
            suffix = 1
            while JournalTag.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base_slug[:50]}-{suffix}"
                suffix += 1
            self.slug = candidate
        super().save(*args, **kwargs)


class JournalEntry(models.Model):
    MOOD_CHOICES = [
        (1, 'Very Low'),
        (2, 'Low'),
        (3, 'Neutral'),
        (4, 'Good'),
        (5, 'Great'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='journal_entries',
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    mood = models.PositiveSmallIntegerField(
        choices=MOOD_CHOICES,
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='How you felt while writing this entry (1-5)',
    )
    entry_date = models.DateField(default=timezone.localdate, db_index=True)
    tags = models.ManyToManyField(JournalTag, blank=True, related_name='entries')

    is_favorite = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)

    word_count = models.PositiveIntegerField(default=0)
    read_count = models.PositiveIntegerField(default=0)
    last_read_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-entry_date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'entry_date']),
            models.Index(fields=['user', 'mood']),
            models.Index(fields=['user', 'is_favorite']),
            models.Index(fields=['user', 'is_archived']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    def save(self, *args, **kwargs):
        self.word_count = len([token for token in self.content.split() if token.strip()])
        super().save(*args, **kwargs)


class JournalReadEvent(models.Model):
    READ_SOURCE_CHOICES = [
        ('manual', 'Manual Open'),
        ('recommendation', 'Recommended Reread'),
        ('reflection', 'Reflection Session'),
    ]

    entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.CASCADE,
        related_name='read_events',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='journal_read_events',
    )
    source = models.CharField(max_length=20, choices=READ_SOURCE_CHOICES, default='manual')
    read_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-read_at']
        indexes = [
            models.Index(fields=['user', 'read_at']),
            models.Index(fields=['entry', 'read_at']),
        ]

    def __str__(self):
        return f"{self.user.username} reread {self.entry_id} at {self.read_at}"


class JournalPrompt(models.Model):
    CATEGORY_CHOICES = [
        ('reflection', 'Reflection'),
        ('gratitude', 'Gratitude'),
        ('stress', 'Stress Processing'),
        ('goals', 'Goals and Direction'),
        ('self_compassion', 'Self Compassion'),
    ]

    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='reflection')
    prompt_text = models.TextField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'id']

    def __str__(self):
        return f"[{self.category}] {self.prompt_text[:60]}"
