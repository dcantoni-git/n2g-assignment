"""
Tests for the message API.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

SEND_TO_EXCHANGE_URL = reverse('message:send_to_exchange')
STORE_TO_DATABASE_URL = reverse('message:store_to_database', args=[10])
SHOW_STORED_MESSAGES_URL = reverse('message:show_stored_messages')


class PublicMessageAPITests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required_consume_data(self):
        """Test auth is required to consume data."""
        res = self.client.get(SEND_TO_EXCHANGE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_auth_required_store_data(self):
        """Test auth is required to store data."""
        res = self.client.get(STORE_TO_DATABASE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_auth_required_show_data(self):
        """Test auth is required to show data.."""
        res = self.client.get(SHOW_STORED_MESSAGES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


class PrivateMessageAPITests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.user_info = {
            'email': 'test@example.com',
            'username': 'Test Username',
            'password': 'Test123!@#',
        }
        self.user = create_user(**self.user_info)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_send_to_exchange(self):
        """Test consuming data from the external API and send them to the exchange."""  # noqa: E501
        res = self.client.get(SEND_TO_EXCHANGE_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_store_to_database(self):
        """Test that the messages were retrieved from the results queue and stored to database."""  # noqa: E501
        res = self.client.get(STORE_TO_DATABASE_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
