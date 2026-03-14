"""
Notification views + rules engine.

Rules (hard-and-fast):
  1. Motivational quote   – at most one per 48 hours per user.
  2. Exercise reminder    – if no completed exercise Activity exists for today.
  3. Weekly stats         – one per week (Mon–Sun), generated on Sunday or first
						   request after Sunday.
  4. Journal reminder     – if the user has no JournalEntry in the last 3 days.

The client calls POST /api/notifications/generate/ (or the server can call it
via a scheduled task / cron) to evaluate and persist new notifications.
GET /api/notifications/          → list unread (or all) notifications.
POST /api/notifications/mark-read/ → mark one or many as read.
"""

from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, PolymorphicProxySerializer, extend_schema
from drf_spectacular.types import OpenApiTypes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from notifications.models import Notification, MotivationalQuote
from notifications.serializers import (
	ExerciseReminderNotificationSchemaSerializer,
	GenerateNotificationsResponseSerializer,
	JournalReminderNotificationSchemaSerializer,
	MarkReadRequestSerializer,
	MarkReadResponseSerializer,
	MotivationalQuoteNotificationSchemaSerializer,
	NotificationSerializer,
	WeeklyStatsNotificationSchemaSerializer,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _latest_notification(user, ntype):
	return (
		Notification.objects.filter(user=user, notification_type=ntype)
		.order_by('-created_at')
		.first()
	)


def _hours_since(notification):
	if notification is None:
		return float('inf')
	return (timezone.now() - notification.created_at).total_seconds() / 3600


def _week_number(dt):
	"""ISO week number + year as a unique string, e.g. '2026-W11'."""
	iso = dt.isocalendar()
	return f'{iso[0]}-W{iso[1]:02d}'


# ── rule: motivational quote every 48 h ──────────────────────────────────────

def _maybe_quote(user):
	last = _latest_notification(user, Notification.Type.MOTIVATIONAL_QUOTE)
	if _hours_since(last) < 48:
		return None

	quote = MotivationalQuote.objects.order_by('?').first()
	if not quote:
		text   = 'Small steps every day lead to big changes over time.'
		author = ''
	else:
		text   = quote.text
		author = quote.author

	return Notification(
		user=user,
		notification_type=Notification.Type.MOTIVATIONAL_QUOTE,
		title='Your daily motivation \U0001f4aa',
		message=f'"{text}"' + (f'  \u2014 {author}' if author else ''),
		payload={'quote': text, 'author': author},
	)


# ── rule: exercise reminder if no exercise completed today ───────────────────

def _maybe_exercise_reminder(user):
	from workout.models import Activity

	today = timezone.localdate()
	exercised_today = Activity.objects.filter(
		user=user,
		activity_type='exercise',
		completed=True,
		completion_date__date=today,
	).exists()

	if exercised_today:
		return None

	# Avoid spamming – only one per calendar day
	last = _latest_notification(user, Notification.Type.EXERCISE_REMINDER)
	if last and last.created_at.date() == today:
		return None

	return Notification(
		user=user,
		notification_type=Notification.Type.EXERCISE_REMINDER,
		title="You haven't exercised today \U0001f3c3",
		message=(
			'Your body thrives on movement. Even a 20-minute walk counts \u2014 '
			'open your recommended activities and pick something that fits your energy right now.'
		),
		payload={'date': today.isoformat()},
	)


# ── rule: weekly stats on Sunday (or first poll after Sunday) ────────────────

def _maybe_weekly_stats(user):
	from workout.models import Activity

	today        = timezone.localdate()
	current_week = _week_number(today)

	last = _latest_notification(user, Notification.Type.WEEKLY_STATS)
	if last and _week_number(last.created_at.date()) == current_week:
		return None  # already sent this week

	# Only generate from Sunday onward (weekday 6 = Sunday in Python)
	if today.weekday() != 6:
		return None

	# Calculate week window (Mon–Sun)
	week_start = today - timedelta(days=6)

	activities = Activity.objects.filter(
		user=user,
		completed=True,
		completion_date__date__gte=week_start,
		completion_date__date__lte=today,
	)

	total       = activities.count()
	exercises   = activities.filter(activity_type='exercise').count()
	meditations = activities.filter(activity_type='meditation').count()
	journaling  = activities.filter(activity_type='journaling').count()
	total_mins  = activities.aggregate(t=Sum('duration_minutes'))['t'] or 0

	motivated_qs = activities.filter(motivation_after__isnull=False)
	if motivated_qs.exists():
		avg_mot = round(
			sum(a.motivation_after for a in motivated_qs) / motivated_qs.count(), 1
		)
	else:
		avg_mot = None

	stats = {
		'week': current_week,
		'total_activities': total,
		'exercises': exercises,
		'meditations': meditations,
		'journaling': journaling,
		'total_minutes': total_mins,
		'avg_motivation_after': avg_mot,
	}

	if total == 0:
		msg = (
			f'No activities completed this week ({week_start} \u2013 {today}). '
			"A fresh week starts tomorrow \u2014 let's make it count!"
		)
	else:
		msg = (
			f'Week {current_week} recap: {total} activities completed '
			f'({exercises} exercise, {meditations} meditation, {journaling} journaling), '
			f'{total_mins} total minutes.'
			+ (f' Average post-activity motivation: {avg_mot}/5.' if avg_mot else '')
		)

	return Notification(
		user=user,
		notification_type=Notification.Type.WEEKLY_STATS,
		title=f'Your week in review \U0001f4ca ({current_week})',
		message=msg,
		payload=stats,
	)


# ── rule: journal reminder if no entry in 3 days ─────────────────────────────

def _maybe_journal_reminder(user):
	from journal.models import JournalEntry

	three_days_ago = timezone.localdate() - timedelta(days=3)
	has_recent = JournalEntry.objects.filter(
		user=user,
		entry_date__gte=three_days_ago,
	).exists()

	if has_recent:
		return None

	# At most one reminder per 3-day window
	last = _latest_notification(user, Notification.Type.JOURNAL_REMINDER)
	if last and (timezone.now() - last.created_at).days < 3:
		return None

	return Notification(
		user=user,
		notification_type=Notification.Type.JOURNAL_REMINDER,
		title="It's been a while since you journaled \U0001f4d3",
		message=(
			"You haven't written a journal entry in over 3 days. "
			'Even a few sentences can help you process your thoughts and track your progress. '
			'Try a CBT thought-record or just free-write \u2014 whatever feels right today.'
		),
		payload={'last_entry_check': three_days_ago.isoformat()},
	)


# ── views ─────────────────────────────────────────────────────────────────────

class NotificationListView(APIView):
	permission_classes = [IsAuthenticated]

	@extend_schema(
		tags=['Notifications'],
		summary='List notifications',
		description=(
			'Returns notifications for the authenticated user, newest first.\n\n'
			'**Notification types and their rules:**\n\n'
			'| Type | Rule |\n'
			'|---|---|\n'
			'| `motivational_quote` | Sent at most once every **48 hours** |\n'
			'| `exercise_reminder` | Sent if no exercise completed **today** (once per day) |\n'
			'| `weekly_stats` | Sent once per week on **Sunday** with a full activity summary |\n'
			'| `journal_reminder` | Sent if no journal entry in the last **3 days** |\n\n'
			'Use `?unread_only=true` to fetch only unread notifications.\n\n'
			'Call `POST /api/notifications/generate/` first to evaluate and create pending notifications.'
		),
		parameters=[
			OpenApiParameter(
				name='unread_only',
				type=OpenApiTypes.BOOL,
				location=OpenApiParameter.QUERY,
				required=False,
				description='If true, returns only unread notifications.',
			),
		],
		responses={
			200: PolymorphicProxySerializer(
				component_name='NotificationItem',
				serializers=[
					MotivationalQuoteNotificationSchemaSerializer,
					ExerciseReminderNotificationSchemaSerializer,
					WeeklyStatsNotificationSchemaSerializer,
					JournalReminderNotificationSchemaSerializer,
				],
				resource_type_field_name='notification_type',
				many=True,
			),
		},
	)
	def get(self, request):
		qs = Notification.objects.filter(user=request.user)
		if request.query_params.get('unread_only', '').lower() in ('true', '1'):
			qs = qs.filter(is_read=False)
		return Response(NotificationSerializer(qs[:50], many=True).data)


class GenerateNotificationsView(APIView):
	permission_classes = [IsAuthenticated]

	@extend_schema(
		tags=['Notifications'],
		summary='Evaluate and generate pending notifications',
		description=(
			"Runs all four notification rules against the authenticated user's data "
			'and persists any new notifications that are due.\n\n'
			'**Rules evaluated:**\n'
			'- Motivational quote if \u2265 48 h since last one\n'
			'- Exercise reminder if no exercise completed today\n'
			'- Weekly stats if today is Sunday and none sent yet this week\n'
			'- Journal reminder if no entry in the last 3 days\n\n'
			'Safe to call on every app open \u2014 each rule is idempotent and will '
			'not create duplicates within its cool-down window.\n\n'
			'Returns a count of newly created notifications and a per-type breakdown.'
		),
		responses={200: GenerateNotificationsResponseSerializer},
	)
	def post(self, request):
		user = request.user
		rules = [
			_maybe_quote,
			_maybe_exercise_reminder,
			_maybe_weekly_stats,
			_maybe_journal_reminder,
		]

		to_create = []
		breakdown = {}
		for rule in rules:
			notif = rule(user)
			if notif:
				to_create.append(notif)
				key = notif.notification_type
				breakdown[key] = breakdown.get(key, 0) + 1

		if to_create:
			Notification.objects.bulk_create(to_create)

		return Response(
			{'generated': len(to_create), 'breakdown': breakdown},
			status=status.HTTP_200_OK,
		)


class MarkNotificationsReadView(APIView):
	permission_classes = [IsAuthenticated]

	@extend_schema(
		tags=['Notifications'],
		summary='Mark notifications as read',
		description='Marks one or more notifications as read. Only affects notifications belonging to the authenticated user.',
		request=MarkReadRequestSerializer,
		responses={200: MarkReadResponseSerializer},
	)
	def post(self, request):
		serializer = MarkReadRequestSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		updated = (
			Notification.objects
			.filter(
				user=request.user,
				id__in=serializer.validated_data['ids'],
				is_read=False,
			)
			.update(is_read=True, read_at=timezone.now())
		)
		return Response({'marked_read': updated}, status=status.HTTP_200_OK)


class MarkAllNotificationsReadView(APIView):
	permission_classes = [IsAuthenticated]

	@extend_schema(
		tags=['Notifications'],
		summary='Mark all notifications as read',
		description='Marks every unread notification for the authenticated user as read.',
		responses={200: MarkReadResponseSerializer},
	)
	def post(self, request):
		updated = (
			Notification.objects
			.filter(user=request.user, is_read=False)
			.update(is_read=True, read_at=timezone.now())
		)
		return Response({'marked_read': updated}, status=status.HTTP_200_OK)
