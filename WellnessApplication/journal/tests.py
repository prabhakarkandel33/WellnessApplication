from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from journal.models import JournalEntry, JournalPrompt, JournalReadEvent


User = get_user_model()


class JournalAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='journal_user',
            email='journal_user@example.com',
            password='StrongPassword123!',
        )
        self.other_user = User.objects.create_user(
            username='other_user',
            email='other_user@example.com',
            password='StrongPassword123!',
        )

        self.client.force_authenticate(user=self.user)

        self.entries_url = '/api/journal/entries/'
        self.insights_url = '/api/journal/insights/'
        self.random_prompt_url = '/api/journal/prompts/random/'

    def test_create_journal_entry_with_tags(self):
        payload = {
            'title': 'Evening reflection',
            'content': 'Today I stayed consistent with my walk and felt less stressed afterward.',
            'mood': 4,
            'entry_date': timezone.localdate().isoformat(),
            'tag_names': ['stress', 'walking'],
        }

        response = self.client.post(self.entries_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        entry = JournalEntry.objects.get(id=response.data['id'])
        self.assertEqual(entry.user, self.user)
        self.assertEqual(entry.tags.count(), 2)
        self.assertGreater(entry.word_count, 0)

    def test_list_entries_returns_only_authenticated_user_data(self):
        JournalEntry.objects.create(
            user=self.user,
            title='My entry',
            content='This is my own personal journal entry for testing.',
            mood=3,
        )
        JournalEntry.objects.create(
            user=self.other_user,
            title='Other entry',
            content='This should not show up for the authenticated user list.',
            mood=2,
        )

        response = self.client.get(self.entries_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'My entry')

    def test_user_cannot_retrieve_another_users_entry(self):
        other_entry = JournalEntry.objects.create(
            user=self.other_user,
            title='Private entry',
            content='This should not be retrievable by a different authenticated user.',
            mood=2,
        )

        response = self.client.get(f'/api/journal/entries/{other_entry.id}/')

        # ModelViewSet uses user-scoped queryset, so foreign objects resolve as not found.
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_journal_endpoints_require_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.entries_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_reread_endpoint_increments_read_count_and_logs_event(self):
        entry = JournalEntry.objects.create(
            user=self.user,
            title='Reread me',
            content='This entry will be reread and tracked in analytics.',
            mood=3,
        )

        response = self.client.post(
            f'/api/journal/entries/{entry.id}/reread/',
            {'source': 'manual'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        entry.refresh_from_db()
        self.assertEqual(entry.read_count, 1)
        self.assertIsNotNone(entry.last_read_at)
        self.assertEqual(JournalReadEvent.objects.filter(entry=entry, user=self.user).count(), 1)

    def test_insights_endpoint_reports_reread_metrics(self):
        first_entry = JournalEntry.objects.create(
            user=self.user,
            title='First entry',
            content='This is the first entry with enough detail for validation.',
            mood=4,
        )
        JournalEntry.objects.create(
            user=self.user,
            title='Second entry',
            content='This is the second entry and it has enough text as well.',
            mood=3,
        )

        self.client.post(
            f'/api/journal/entries/{first_entry.id}/reread/',
            {'source': 'reflection'},
            format='json',
        )

        response = self.client.get(self.insights_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_entries'], 2)
        self.assertEqual(response.data['reread_entries_count'], 1)
        self.assertEqual(response.data['reread_ratio_percent'], 50.0)

    def test_random_prompt_endpoint_returns_category_filtered_prompt(self):
        JournalPrompt.objects.create(
            category='gratitude',
            prompt_text='What went unexpectedly well today?',
            is_active=True,
        )

        response = self.client.get(self.random_prompt_url, {'category': 'gratitude'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['category'], 'gratitude')
        self.assertIn('prompt_text', response.data)
