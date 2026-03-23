from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase


User = get_user_model()


class SelfProfileAPITestCase(APITestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			username='profile_user',
			email='profile_user@example.com',
			password='StrongPassword123!',
			first_name='Jane',
			last_name='Doe',
			age=28,
			gender='female',
		)
		self.profile_url = '/api/profile/'

	def test_profile_requires_authentication(self):
		response = self.client.get(self.profile_url)
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_profile_returns_authenticated_user_details(self):
		self.client.force_authenticate(user=self.user)

		response = self.client.get(self.profile_url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['id'], self.user.id)
		self.assertEqual(response.data['username'], 'profile_user')
		self.assertEqual(response.data['email'], 'profile_user@example.com')
		self.assertEqual(response.data['first_name'], 'Jane')
		self.assertEqual(response.data['last_name'], 'Doe')
