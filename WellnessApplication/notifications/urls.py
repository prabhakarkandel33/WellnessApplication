from django.urls import path

from notifications.views import (
    GenerateNotificationsView,
    MarkAllNotificationsReadView,
    MarkNotificationsReadView,
    NotificationListView,
)

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification-list'),
    path('generate/', GenerateNotificationsView.as_view(), name='notification-generate'),
    path('mark-read/', MarkNotificationsReadView.as_view(), name='notification-mark-read'),
    path('mark-all-read/', MarkAllNotificationsReadView.as_view(), name='notification-mark-all-read'),
]
