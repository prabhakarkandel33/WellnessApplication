from django.contrib import admin

from notifications.models import MotivationalQuote, Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
	list_display  = ('user', 'notification_type', 'title', 'is_read', 'created_at')
	list_filter   = ('notification_type', 'is_read')
	search_fields = ('user__email', 'title', 'message')
	ordering      = ('-created_at',)
	readonly_fields = ('created_at', 'read_at')


@admin.register(MotivationalQuote)
class MotivationalQuoteAdmin(admin.ModelAdmin):
	list_display  = ('author', 'text')
	search_fields = ('text', 'author')
