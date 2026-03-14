from rest_framework import serializers

from journal.models import JournalEntry, JournalPrompt, JournalReadEvent, JournalTag


class JournalEntryFilterSerializer(serializers.Serializer):
    q = serializers.CharField(required=False, allow_blank=True)
    mood = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=5,
        help_text='Filter by mood using the scale: 1=Very Low, 2=Low, 3=Neutral, 4=Good, 5=Great.',
    )
    is_favorite = serializers.BooleanField(required=False)
    is_archived = serializers.BooleanField(required=False)
    tag = serializers.CharField(required=False, allow_blank=True)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    # CBT filter: pass true to return only entries with a thought record filled in
    has_thought_record = serializers.BooleanField(required=False)

    def validate(self, attrs):
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError('start_date must be before or equal to end_date.')
        return attrs


class JournalTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalTag
        fields = ['id', 'name', 'slug']


# Sorted list of (key, label) pairs – single source of truth for schema + validation.
_DISTORTION_CHOICES = sorted(JournalEntry.COGNITIVE_DISTORTIONS, key=lambda x: x[0])
_DISTORTION_KEYS  = {key for key, _ in _DISTORTION_CHOICES}
_DISTORTION_LABEL = {key: label for key, label in _DISTORTION_CHOICES}


class JournalEntrySerializer(serializers.ModelSerializer):
    tags = JournalTagSerializer(many=True, read_only=True)
    mood = serializers.ChoiceField(
        choices=JournalEntry.MOOD_CHOICES,
        help_text='Mood rating for the entry. Use: 1=Very Low, 2=Low, 3=Neutral, 4=Good, 5=Great.',
    )
    # Explicit typed field so Swagger renders an enum array instead of a generic JSON blob.
    cognitive_distortions = serializers.ListField(
        child=serializers.ChoiceField(
            choices=_DISTORTION_CHOICES,
            help_text='One of the 12 cognitive distortion keys.',
        ),
        default=list,
        required=False,
        allow_empty=True,
        help_text=(
            'Array of cognitive distortion keys identified in this thought record. '
            'Each item must be one of the 12 valid keys. '
            'Valid keys: all_or_nothing, catastrophizing, disqualifying_positive, '
            'emotional_reasoning, evidence_against, fortune_telling, jumping_to_conclusions, '
            'labeling, mental_filter, mind_reading, overgeneralization, '
            'personalization, should_statements.'
        ),
    )
    tag_names = serializers.ListField(
        child=serializers.CharField(max_length=50),
        write_only=True,
        required=False,
        allow_empty=True,
    )
    mood_label = serializers.SerializerMethodField(
        help_text='Human-readable label for the numeric mood value.',
    )
    excerpt = serializers.SerializerMethodField()
    # CBT computed helpers (read-only)
    has_thought_record = serializers.SerializerMethodField()
    cognitive_distortions_display = serializers.SerializerMethodField()
    emotion_shift = serializers.SerializerMethodField()

    class Meta:
        model = JournalEntry
        fields = [
            'id',
            'title',
            'content',
            'excerpt',
            'mood',
            'mood_label',
            'entry_date',
            'tags',
            'tag_names',
            'is_favorite',
            'is_archived',
            'word_count',
            'read_count',
            'last_read_at',
            # ── CBT Thought-Record fields ──
            'situation',
            'automatic_thought',
            'emotion_intensity_before',
            'cognitive_distortions',
            'cognitive_distortions_display',
            'evidence_for',
            'evidence_against',
            'balanced_thought',
            'emotion_intensity_after',
            'behavioral_response',
            # ── computed ──
            'has_thought_record',
            'emotion_shift',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'excerpt',
            'mood_label',
            'tags',
            'word_count',
            'read_count',
            'last_read_at',
            'has_thought_record',
            'cognitive_distortions_display',
            'emotion_shift',
            'created_at',
            'updated_at',
        ]

    def get_mood_label(self, obj):
        return obj.get_mood_display()

    def get_excerpt(self, obj):
        if len(obj.content) <= 160:
            return obj.content
        return f"{obj.content[:157]}..."

    def get_has_thought_record(self, obj):
        """True when at least situation and automatic_thought are filled in."""
        return bool(obj.situation.strip() and obj.automatic_thought.strip())

    def get_cognitive_distortions_display(self, obj):
        """Translate distortion keys to human-readable labels."""
        return [
            {'key': k, 'label': _DISTORTION_LABEL.get(k, k)}
            for k in (obj.cognitive_distortions or [])
        ]

    def get_emotion_shift(self, obj):
        """Difference in emotion intensity after vs before reframing (negative = improved)."""
        if obj.emotion_intensity_before is not None and obj.emotion_intensity_after is not None:
            return obj.emotion_intensity_after - obj.emotion_intensity_before
        return None

    def validate_content(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError('Please provide at least 10 characters in your journal entry.')
        return value

    def validate_cognitive_distortions(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError('cognitive_distortions must be a list of distortion keys.')
        invalid = [k for k in value if k not in _DISTORTION_KEYS]
        if invalid:
            raise serializers.ValidationError(
                f'Unknown cognitive distortion keys: {invalid}. '
                f'Valid keys: {sorted(_DISTORTION_KEYS)}'
            )
        return value

    def validate_tag_names(self, value):
        cleaned = []
        for raw in value:
            name = raw.strip().lower()
            if not name:
                continue
            cleaned.append(name)
        return list(dict.fromkeys(cleaned))

    def create(self, validated_data):
        tag_names = validated_data.pop('tag_names', [])
        entry = JournalEntry.objects.create(**validated_data)
        self._apply_tags(entry, tag_names)
        return entry

    def update(self, instance, validated_data):
        tag_names = validated_data.pop('tag_names', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if tag_names is not None:
            self._apply_tags(instance, tag_names)

        return instance

    def _apply_tags(self, entry, tag_names):
        if not tag_names:
            entry.tags.clear()
            return

        tags = []
        for name in tag_names:
            tag, _ = JournalTag.objects.get_or_create(name=name)
            tags.append(tag)

        entry.tags.set(tags)


class JournalReadEventRequestSerializer(serializers.Serializer):
    source = serializers.ChoiceField(
        choices=JournalReadEvent.READ_SOURCE_CHOICES,
        default='manual',
        required=False,
    )


class JournalReadEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalReadEvent
        fields = ['id', 'source', 'read_at']


class ToggleFavoriteResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    is_favorite = serializers.BooleanField()


class JournalPromptSerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalPrompt
        fields = ['id', 'category', 'prompt_text']


class MoodDistributionSerializer(serializers.Serializer):
    mood = serializers.IntegerField()
    label = serializers.CharField()
    count = serializers.IntegerField()


class TopTagSerializer(serializers.Serializer):
    name = serializers.CharField()
    count = serializers.IntegerField()


class JournalInsightsSerializer(serializers.Serializer):
    total_entries = serializers.IntegerField()
    entries_last_7_days = serializers.IntegerField()
    entries_last_30_days = serializers.IntegerField()
    current_streak_days = serializers.IntegerField()
    longest_streak_days = serializers.IntegerField()
    average_word_count = serializers.FloatField()
    total_rereads = serializers.IntegerField()
    reread_entries_count = serializers.IntegerField()
    reread_ratio_percent = serializers.FloatField()
    most_common_mood = serializers.CharField(allow_null=True)
    mood_distribution = MoodDistributionSerializer(many=True)
    top_tags = TopTagSerializer(many=True)
    last_entry_at = serializers.DateTimeField(allow_null=True)
    # CBT analytics
    thought_records_total = serializers.IntegerField()
    avg_emotion_shift = serializers.FloatField(allow_null=True)
    top_distortions = serializers.ListField(child=serializers.DictField())


# ── CBT Guide serializers ──────────────────────────────────────────────────────

class CognitivDistortionSerializer(serializers.Serializer):
    key = serializers.CharField()
    label = serializers.CharField()
    description = serializers.CharField()
    example = serializers.CharField()


class CBTStepSerializer(serializers.Serializer):
    step = serializers.IntegerField()
    title = serializers.CharField()
    field = serializers.CharField()
    instruction = serializers.CharField()
    tip = serializers.CharField()


class CBTGuideSerializer(serializers.Serializer):
    title = serializers.CharField()
    summary = serializers.CharField()
    steps = CBTStepSerializer(many=True)
    cognitive_distortions = CognitivDistortionSerializer(many=True)
    valid_distortion_keys = serializers.ListField(child=serializers.CharField())
