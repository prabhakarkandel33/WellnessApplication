import statistics as _stats
from datetime import timedelta

from django.db.models import Avg, Count, F, Q
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from journal.models import JournalEntry, JournalPrompt, JournalReadEvent, JournalTag
from journal.serializers import (
    CBTGuideSerializer,
    JournalEntryFilterSerializer,
    JournalEntrySerializer,
    JournalInsightsSerializer,
    JournalPromptSerializer,
    JournalReadEventRequestSerializer,
    ToggleFavoriteResponseSerializer,
)


def _compute_streaks(entry_dates):
    if not entry_dates:
        return 0, 0

    unique_dates = sorted(set(entry_dates))

    longest_streak = 1
    running_streak = 1
    for index in range(1, len(unique_dates)):
        if (unique_dates[index] - unique_dates[index - 1]).days == 1:
            running_streak += 1
            longest_streak = max(longest_streak, running_streak)
        else:
            running_streak = 1

    today = timezone.localdate()
    check_date = today
    date_set = set(unique_dates)

    # If today has no entry yet, allow the streak to continue from yesterday.
    if check_date not in date_set:
        check_date = today - timedelta(days=1)

    current_streak = 0
    while check_date in date_set:
        current_streak += 1
        check_date -= timedelta(days=1)

    return current_streak, longest_streak


_ENTRY_CBT_DESCRIPTION = """
**Mood scale**

- `1` = Very Low
- `2` = Low
- `3` = Neutral
- `4` = Good
- `5` = Great

**CBT Thought-Record fields** (all optional — omit them for a plain free-form entry):

| Field | CBT Step | Notes |
|---|---|---|
| `situation` | 1 – Situation | Brief description of the triggering event |
| `automatic_thought` | 2 – Automatic Thought | Raw thought, word-for-word |
| `emotion_intensity_before` | 3 – Emotion Intensity | Integer 0–100 before reframing |
| `cognitive_distortions` | 4 – Distortions | Array of distortion keys — **must be one or more of the exact values below** |

**Valid `cognitive_distortions` keys** (send as a JSON array of strings, or `[]` to clear):

| Key | Label |
|---|---|
| `all_or_nothing` | All-or-Nothing Thinking |
| `catastrophizing` | Catastrophizing |
| `disqualifying_positive` | Disqualifying the Positive |
| `emotional_reasoning` | Emotional Reasoning |
| `fortune_telling` | Fortune Telling |
| `jumping_to_conclusions` | Jumping to Conclusions |
| `labeling` | Labeling |
| `mental_filter` | Mental Filter |
| `mind_reading` | Mind Reading |
| `overgeneralization` | Overgeneralization |
| `personalization` | Personalization |
| `should_statements` | "Should" Statements |

Example: `"cognitive_distortions": ["catastrophizing", "mind_reading"]`
| `evidence_for` | 5a – Evidence For | Facts supporting the thought |
| `evidence_against` | 5b – Evidence Against | Facts challenging the thought |
| `balanced_thought` | 6 – Balanced Thought | Reframed, realistic alternative |
| `emotion_intensity_after` | 7 – Emotion Intensity | Integer 0–100 after reframing |
| `behavioral_response` | 8 – Action | One concrete step to take |

**Read-only computed fields returned in the response:**
- `has_thought_record` — `true` when situation + automatic_thought are present
- `cognitive_distortions_display` — distortion keys expanded to human labels
- `emotion_shift` — `intensity_after - intensity_before` (negative means improvement)

See `GET /api/journal/cbt-guide/` for the full step-by-step guide and valid distortion keys.
"""


@extend_schema_view(
    list=extend_schema(
        tags=['Journal'],
        summary='List journal entries',
        description=(
            'Returns journal entries for the authenticated user with optional filters.\n\n'
            'Filter `?has_thought_record=true` to return only CBT thought-record entries.\n\n'
            + _ENTRY_CBT_DESCRIPTION
        ),
        parameters=[JournalEntryFilterSerializer],
        responses={200: JournalEntrySerializer(many=True)},
    ),
    create=extend_schema(
        tags=['Journal'],
        summary='Create journal entry',
        description=(
            'Creates a new journal entry for the authenticated user.\n\n'
            + _ENTRY_CBT_DESCRIPTION
        ),
        request=JournalEntrySerializer,
        responses={201: JournalEntrySerializer},
    ),
    retrieve=extend_schema(
        tags=['Journal'],
        summary='Get journal entry',
        description='Returns a single journal entry. Includes all CBT thought-record fields if populated.',
        responses={200: JournalEntrySerializer},
    ),
    partial_update=extend_schema(
        tags=['Journal'],
        summary='Update journal entry',
        description=(
            'Partially update a journal entry. You can add or fill in CBT '
            'thought-record fields at any time after the initial save.\n\n'
            + _ENTRY_CBT_DESCRIPTION
        ),
        request=JournalEntrySerializer,
        responses={200: JournalEntrySerializer},
    ),
    destroy=extend_schema(
        tags=['Journal'],
        summary='Delete journal entry',
        responses={204: None},
    ),
)
class JournalEntryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = JournalEntrySerializer

    def get_queryset(self):
        queryset = JournalEntry.objects.filter(user=self.request.user).prefetch_related('tags')

        filter_serializer = JournalEntryFilterSerializer(data=self.request.query_params)
        filter_serializer.is_valid(raise_exception=True)
        filters = filter_serializer.validated_data

        query_text = filters.get('q')
        if query_text:
            queryset = queryset.filter(Q(title__icontains=query_text) | Q(content__icontains=query_text))

        mood = filters.get('mood')
        if mood:
            queryset = queryset.filter(mood=mood)

        if 'is_favorite' in filters:
            queryset = queryset.filter(is_favorite=filters['is_favorite'])

        if 'is_archived' in filters:
            queryset = queryset.filter(is_archived=filters['is_archived'])

        tag_name = filters.get('tag')
        if tag_name:
            queryset = queryset.filter(tags__name__iexact=tag_name.strip().lower())

        start_date = filters.get('start_date')
        if start_date:
            queryset = queryset.filter(entry_date__gte=start_date)

        end_date = filters.get('end_date')
        if end_date:
            queryset = queryset.filter(entry_date__lte=end_date)

        if 'has_thought_record' in filters:
            if filters['has_thought_record']:
                queryset = queryset.exclude(situation='').exclude(automatic_thought='')
            else:
                queryset = queryset.filter(Q(situation='') | Q(automatic_thought=''))

        return queryset.distinct()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @extend_schema(
        tags=['Journal'],
        summary='Track journal reread',
        description='Creates a reread event and increments read counters for analytics.',
        request=JournalReadEventRequestSerializer,
        responses={200: JournalEntrySerializer},
    )
    @action(detail=True, methods=['post'])
    def reread(self, request, pk=None):
        entry = self.get_object()

        request_serializer = JournalReadEventRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        source = request_serializer.validated_data.get('source', 'manual')

        JournalReadEvent.objects.create(entry=entry, user=request.user, source=source)

        JournalEntry.objects.filter(pk=entry.pk).update(
            read_count=F('read_count') + 1,
            last_read_at=timezone.now(),
        )
        entry.refresh_from_db(fields=['read_count', 'last_read_at'])

        response_serializer = self.get_serializer(entry)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=['Journal'],
        summary='Toggle favorite',
        responses={200: ToggleFavoriteResponseSerializer},
    )
    @action(detail=True, methods=['post'], url_path='toggle-favorite')
    def toggle_favorite(self, request, pk=None):
        entry = self.get_object()
        entry.is_favorite = not entry.is_favorite
        entry.save(update_fields=['is_favorite', 'updated_at'])

        return Response(
            {
                'id': entry.id,
                'is_favorite': entry.is_favorite,
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(
    tags=['Journal'],
    summary='Get journaling insights',
    description=(
        'Returns aggregated analytics for the authenticated user.\n\n'
        '**Standard analytics:** entry counts, current and longest streaks, '
        'average word count, reread totals and ratio, mood distribution, top tags.\n\n'
        '**CBT analytics:** `thought_records_total` — how many entries have a thought record; '
        '`avg_emotion_shift` — average change in emotion intensity across completed thought records '
        '(negative = improvement); `top_distortions` — the five most frequently identified '
        'cognitive distortions across all entries.'
    ),
    responses={200: JournalInsightsSerializer},
)
class JournalInsightsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        entries = JournalEntry.objects.filter(user=user)

        total_entries = entries.count()
        today = timezone.localdate()

        entries_last_7_days = entries.filter(entry_date__gte=today - timedelta(days=6)).count()
        entries_last_30_days = entries.filter(entry_date__gte=today - timedelta(days=29)).count()

        entry_dates = list(entries.values_list('entry_date', flat=True))
        current_streak, longest_streak = _compute_streaks(entry_dates)

        average_word_count = float(entries.aggregate(avg=Avg('word_count'))['avg'] or 0.0)

        total_rereads = JournalReadEvent.objects.filter(user=user).count()
        reread_entries_count = entries.filter(read_count__gt=0).count()
        reread_ratio_percent = (reread_entries_count / total_entries * 100.0) if total_entries else 0.0

        mood_counts = entries.values('mood').annotate(count=Count('id')).order_by('mood')
        mood_lookup = dict(JournalEntry.MOOD_CHOICES)
        mood_distribution = [
            {
                'mood': row['mood'],
                'label': mood_lookup.get(row['mood'], 'Unknown'),
                'count': row['count'],
            }
            for row in mood_counts
        ]

        top_mood = entries.values('mood').annotate(count=Count('id')).order_by('-count', 'mood').first()
        most_common_mood = mood_lookup.get(top_mood['mood']) if top_mood else None

        top_tags_queryset = JournalTag.objects.filter(entries__user=user).annotate(
            count=Count('entries', filter=Q(entries__user=user)),
        ).order_by('-count', 'name')[:5]

        top_tags = [
            {
                'name': tag.name,
                'count': tag.count,
            }
            for tag in top_tags_queryset
        ]

        last_entry_at = entries.order_by('-created_at').values_list('created_at', flat=True).first()

        # ── CBT analytics ───────────────────────────────────────────────────────────────
        thought_records = entries.exclude(situation='').exclude(automatic_thought='')
        thought_records_total = thought_records.count()

        # Average emotion shift (intensity_after - intensity_before) across thought records
        shifts = [
            (row['emotion_intensity_after'] - row['emotion_intensity_before'])
            for row in thought_records.filter(
                emotion_intensity_before__isnull=False,
                emotion_intensity_after__isnull=False,
            ).values('emotion_intensity_before', 'emotion_intensity_after')
        ]
        avg_emotion_shift = round(_stats.mean(shifts), 2) if shifts else None

        # Count how many times each distortion key appears across all thought records
        distortion_counter: dict = {}
        for row in thought_records.values_list('cognitive_distortions', flat=True):
            for key in (row or []):
                distortion_counter[key] = distortion_counter.get(key, 0) + 1
        distortion_label_map = dict(JournalEntry.COGNITIVE_DISTORTIONS)
        top_distortions = [
            {'key': k, 'label': distortion_label_map.get(k, k), 'count': v}
            for k, v in sorted(distortion_counter.items(), key=lambda x: -x[1])
        ][:5]

        payload = {
            'total_entries': total_entries,
            'entries_last_7_days': entries_last_7_days,
            'entries_last_30_days': entries_last_30_days,
            'current_streak_days': current_streak,
            'longest_streak_days': longest_streak,
            'average_word_count': round(average_word_count, 2),
            'total_rereads': total_rereads,
            'reread_entries_count': reread_entries_count,
            'reread_ratio_percent': round(reread_ratio_percent, 2),
            'most_common_mood': most_common_mood,
            'mood_distribution': mood_distribution,
            'top_tags': top_tags,
            'last_entry_at': last_entry_at,
            'thought_records_total': thought_records_total,
            'avg_emotion_shift': avg_emotion_shift,
            'top_distortions': top_distortions,
        }

        serializer = JournalInsightsSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Journal'],
    summary='Get random journaling prompt',
    description='Returns a random active prompt. Optionally filter by prompt category.',
    parameters=[
        OpenApiParameter(
            name='category',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            required=False,
            enum=[choice[0] for choice in JournalPrompt.CATEGORY_CHOICES],
            description='Prompt category filter.',
        )
    ],
    responses={200: JournalPromptSerializer},
)
class RandomJournalPromptView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        category = request.query_params.get('category')

        queryset = JournalPrompt.objects.filter(is_active=True)
        if category:
            valid_categories = {choice[0] for choice in JournalPrompt.CATEGORY_CHOICES}
            if category not in valid_categories:
                return Response(
                    {'detail': 'Invalid category.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            queryset = queryset.filter(category=category)

        prompt = queryset.order_by('?').first()
        if not prompt:
            return Response(
                {'detail': 'No active prompts available for the selected category.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = JournalPromptSerializer(prompt)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ── CBT Guide ─────────────────────────────────────────────────────────────────

_CBT_GUIDE_PAYLOAD = {
    'title': 'CBT Thought-Record Journaling Guide',
    'summary': (
        'A CBT thought record is a structured technique from Cognitive Behavioral Therapy that '
        'helps you identify and reframe unhelpful automatic thoughts. '
        'Work through the 8 steps below each time you notice a strong negative emotion. '
        'You do NOT need to fill in every field — even completing steps 1-3 is beneficial.'
    ),
    'steps': [
        {
            'step': 1,
            'title': 'Describe the Situation',
            'field': 'situation',
            'instruction': (
                'Write a brief, factual description of where you were, what you were doing, '
                'and who was present when the upsetting feeling began. '
                'Stick to observable facts — no interpretations yet.'
            ),
            'tip': 'Example: "I was in a team meeting and my manager pointed out an error in my report."',
        },
        {
            'step': 2,
            'title': 'Record the Automatic Thought',
            'field': 'automatic_thought',
            'instruction': (
                'Write the exact thought that flashed through your mind in that moment — '
                'word for word, as if you could screenshot your inner dialogue. '
                'Automatic thoughts are often absolute, harsh, or catastrophic.'
            ),
            'tip': 'Example: "Everyone thinks I am incompetent. I am going to get fired."',
        },
        {
            'step': 3,
            'title': 'Rate Your Emotion Intensity (Before)',
            'field': 'emotion_intensity_before',
            'instruction': (
                'On a scale from 0 to 100, how intense is the emotion RIGHT NOW as you write this? '
                '0 = no distress at all, 50 = moderate, 100 = the worst you have ever felt. '
                'You can name the emotion in your main content field (e.g. "anxiety 70/100").'
            ),
            'tip': 'Being specific about intensity helps you measure real change at step 7.',
        },
        {
            'step': 4,
            'title': 'Identify Cognitive Distortions',
            'field': 'cognitive_distortions',
            'instruction': (
                'Look at your automatic thought and check which thinking traps it falls into. '
                'Send an array of keys from the list below. '
                'It is normal to have more than one.'
            ),
            'tip': 'Example: ["catastrophizing", "mind_reading", "fortune_telling"]',
        },
        {
            'step': 5,
            'title': 'Examine the Evidence',
            'field': 'evidence_for / evidence_against',
            'instruction': (
                'In `evidence_for`, list only hard facts (not feelings or assumptions) '
                'that genuinely support your automatic thought. '
                'In `evidence_against`, list facts that challenge or contradict it. '
                'Be as objective as a scientist — both fields count.'
            ),
            'tip': (
                'Evidence FOR: "My manager did point out a specific error." '
                'Evidence AGAINST: "I have received positive feedback on the last three reports. '
                'My manager also said the overall analysis was solid."'
            ),
        },
        {
            'step': 6,
            'title': 'Write a Balanced Thought',
            'field': 'balanced_thought',
            'instruction': (
                'Using the evidence from both sides, write a new thought that is realistic '
                'and compassionate — not falsely positive, just more accurate. '
                'A balanced thought acknowledges the difficulty while keeping perspective.'
            ),
            'tip': (
                'Example: "I made an error today. That is uncomfortable, but one mistake does not '
                'define my competence. My track record shows I am generally reliable, '
                'and I can fix this."'
            ),
        },
        {
            'step': 7,
            'title': 'Re-rate Your Emotion Intensity (After)',
            'field': 'emotion_intensity_after',
            'instruction': (
                'Now that you have written the balanced thought, rate how intense '
                'the same emotion feels on the same 0-100 scale. '
                'The `emotion_shift` field in the response will show the difference automatically '
                '(a negative number means your distress decreased).'
            ),
            'tip': 'Even a small decrease (e.g. 70 → 55) shows the technique is working.',
        },
        {
            'step': 8,
            'title': 'Plan a Behavioral Response',
            'field': 'behavioral_response',
            'instruction': (
                'Name ONE small, concrete action you will take based on your balanced perspective. '
                'This closes the loop between thought and behavior — a core CBT principle.'
            ),
            'tip': (
                'Example: "I will review the report, send a correction to my manager today, '
                'and let myself move on."'
            ),
        },
    ],
    'cognitive_distortions': [
        {
            'key': 'all_or_nothing',
            'label': 'All-or-Nothing Thinking',
            'description': 'Seeing things in black and white with no middle ground.',
            'example': '"If I am not perfect, I am a total failure."',
        },
        {
            'key': 'overgeneralization',
            'label': 'Overgeneralization',
            'description': 'Drawing a sweeping conclusion from a single event.',
            'example': '"I failed this once, so I always fail."',
        },
        {
            'key': 'mental_filter',
            'label': 'Mental Filter',
            'description': 'Focusing exclusively on one negative detail while ignoring positives.',
            'example': '"Someone criticized one thing, so the whole thing was a disaster."',
        },
        {
            'key': 'disqualifying_positive',
            'label': 'Disqualifying the Positive',
            'description': 'Dismissing positive experiences as not counting.',
            'example': '"They only said that to be nice — it does not really count."',
        },
        {
            'key': 'mind_reading',
            'label': 'Mind Reading',
            'description': 'Assuming you know what others think without evidence.',
            'example': '"They are definitely judging me right now."',
        },
        {
            'key': 'fortune_telling',
            'label': 'Fortune Telling',
            'description': 'Predicting a negative outcome as though it is already certain.',
            'example': '"I know I am going to mess this up."',
        },
        {
            'key': 'catastrophizing',
            'label': 'Catastrophizing',
            'description': 'Magnifying problems or imagining worst-case scenarios.',
            'example': '"If I make one mistake, my career is over."',
        },
        {
            'key': 'emotional_reasoning',
            'label': 'Emotional Reasoning',
            'description': 'Treating feelings as facts.',
            'example': '"I feel stupid, therefore I must be stupid."',
        },
        {
            'key': 'should_statements',
            'label': '"Should" Statements',
            'description': 'Rigid rules about how you or others must behave.',
            'example': '"I should always be productive. I must never disappoint anyone."',
        },
        {
            'key': 'labeling',
            'label': 'Labeling',
            'description': 'Attaching a global negative label rather than describing a specific behavior.',
            'example': '"I am a loser" instead of "I did not perform well on that task."',
        },
        {
            'key': 'personalization',
            'label': 'Personalization',
            'description': 'Blaming yourself for events outside your control.',
            'example': '"My friend is upset — I must have done something wrong."',
        },
        {
            'key': 'jumping_to_conclusions',
            'label': 'Jumping to Conclusions',
            'description': 'Reaching negative conclusions without sufficient evidence.',
            'example': '"They did not reply instantly — they must be angry with me."',
        },
    ],
    'valid_distortion_keys': [
        'all_or_nothing', 'overgeneralization', 'mental_filter',
        'disqualifying_positive', 'mind_reading', 'fortune_telling',
        'catastrophizing', 'emotional_reasoning', 'should_statements',
        'labeling', 'personalization', 'jumping_to_conclusions',
    ],
}


@extend_schema(
    tags=['Journal'],
    summary='CBT journaling guide',
    description=(
        'Returns a complete, human-readable guide to CBT thought-record journaling: '
        'what each field means, step-by-step instructions, practical examples, '
        'and the full list of valid cognitive distortion keys accepted by the API. '
        'Designed to be displayed in an in-app "Help / How it works" screen.'
    ),
    responses={200: CBTGuideSerializer},
)
class CBTGuideView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from journal.serializers import CBTGuideSerializer as _S
        serializer = _S(data=_CBT_GUIDE_PAYLOAD)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
