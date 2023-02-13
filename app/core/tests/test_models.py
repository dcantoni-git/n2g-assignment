"""
Tests for models.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from core import models


class ModelTests(TestCase):
    """Test models."""

    def test_create_user_with_email(self):
        """Test creating a user with an email is successful"""
        email = 'test@example.com'
        username = 'test'
        password = 'testpass123'
        user = get_user_model().objects.create_user(
            email=email,
            username=username,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertEqual(user.username, username)
        self.assertTrue(user.check_password(password))

    def test_create_message(self):
        """Test creating a message is successful."""
        user = get_user_model().objects.create_user(
            email='test@example.com',
            username='test_user',
            password='wqe231@!#E',
        )
        message = models.Message.objects.create(
            user=user,
            gatewayEui='84df0c0074808afc',
            profileId='0x0104',
            endpointId='0x0b',
            clusterId='0x0702',
            attributeId='0x0000',
            value=121589,
            timestamp=1676317432527,
        )

        self.assertEqual(str(message), message.gatewayEui)
