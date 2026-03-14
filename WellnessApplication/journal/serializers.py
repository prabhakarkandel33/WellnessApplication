from rest_framework import serializers

from journal.models import JournalEntry, JournalPrompt, JournalReadEvent, JournalTag


class JournalEntryFilterSerializer(serializers.Serializer):
    q = serializers.CharField(required=False, allow_blank=True)
    mood = serializers.IntegerField(required=False, min_value=1, max_value=5)
    is_favorite = serializers.BooleanField(required=False)
    is_archived = serializers.BooleanField(required=False)
    tag = serializers.CharField(required=False, allow_blank=True)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)

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


class JournalEntrySerializer(serializers.ModelSerializer):
    tags = JournalTagSerializer(many=True, read_only=True)
    tag_names = serializers.ListField(
        child=serializers.CharField(max_length=50),
        write_only=True,
        required=False,
        allow_empty=True,
    )
    mood_label = serializers.SerializerMethodField()
    excerpt = serializers.SerializerMethodField()

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
            'created_at',
            'updated_at',
        ]

    def get_mood_label(self, obj):
        return obj.get_mood_display()

    def get_excerpt(self, obj):
        if len(obj.content) <= 160:
            return obj.content
        return f"{obj.content[:157]}..."

    def validate_content(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError('Please provide at least 10 characters in your journal entry.')
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
