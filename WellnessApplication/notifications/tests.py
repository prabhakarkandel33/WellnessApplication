from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from notifications.models import MotivationalQuote
from notifications.quote_catalog import MOTIVATIONAL_QUOTES


class FloodMotivationalQuotesCommandTests(TestCase):
	def test_command_loads_catalog_and_is_idempotent(self):
		initial_count = MotivationalQuote.objects.count()

		command_output = StringIO()
		call_command('flood_motivational_quotes', stdout=command_output)

		first_count = MotivationalQuote.objects.count()
		self.assertGreater(first_count, initial_count)
		self.assertGreaterEqual(first_count, len(MOTIVATIONAL_QUOTES))
		self.assertTrue(
			MotivationalQuote.objects.filter(text=MOTIVATIONAL_QUOTES[0][0]).exists()
		)

		call_command('flood_motivational_quotes')

		self.assertEqual(MotivationalQuote.objects.count(), first_count)
