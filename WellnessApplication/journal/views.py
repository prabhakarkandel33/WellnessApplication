from datetime import timedelta

from django.db.models import Avg, Count, F, Q
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from journal.models import JournalEntry, JournalPrompt, JournalReadEvent, JournalTag
from journal.serializers import (
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


@extend_schema_view(
    list=extend_schema(
        tags=['Journal'],
        summary='List journal entries',
        description='Returns journal entries for the authenticated user with optional filters.',
        parameters=[JournalEntryFilterSerializer],
        responses={200: JournalEntrySerializer(many=True)},
    ),
    create=extend_schema(
        tags=['Journal'],
        summary='Create journal entry',
        request=JournalEntrySerializer,
        responses={201: JournalEntrySerializer},
    ),
    retrieve=extend_schema(
        tags=['Journal'],
        summary='Get journal entry',
        responses={200: JournalEntrySerializer},
    ),
    partial_update=extend_schema(
        tags=['Journal'],
        summary='Update journal entry',
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
    description='Returns consistency, reread behavior, mood distribution, and top tags.',
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
