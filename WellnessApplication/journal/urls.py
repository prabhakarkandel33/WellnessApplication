from django.urls import path
from rest_framework.routers import DefaultRouter

from journal.views import CBTGuideView, JournalEntryViewSet, JournalInsightsView, RandomJournalPromptView


router = DefaultRouter()
router.register('entries', JournalEntryViewSet, basename='journal-entry')


urlpatterns = [
    path('insights/', JournalInsightsView.as_view(), name='journal-insights'),
    path('prompts/random/', RandomJournalPromptView.as_view(), name='journal-random-prompt'),
    path('cbt-guide/', CBTGuideView.as_view(), name='journal-cbt-guide'),
]

urlpatterns += router.urls
