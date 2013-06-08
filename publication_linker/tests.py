"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.core.urlresolvers import reverse


class SimpleTest(TestCase):
    def test_a_view(self):

        data_bad_fields = {
            'not_a_field': 43
        }

        # Using bad fields shouldn't redirect, should give a 200 to same page
        response = self.client.post(
            reverse('home'),
            data=data_bad_fields)
        self.assertEqual(response.status_code, 302)
