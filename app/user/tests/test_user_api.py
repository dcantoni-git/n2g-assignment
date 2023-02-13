"""
Tests for the user API.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Test the public features of the user API."""

    def setUp(self):
        self.client = APIClient()
        self.user_info = {
            'email': 'test@example.com',
            'username': 'Test Username',
            'password': 'Test123!@#',
        }

    def test_create_user_success(self):
        """Test creating a user is successful."""
        res = self.client.post(CREATE_USER_URL, self.user_info)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=self.user_info['email'])
        self.assertTrue(user.check_password(self.user_info['password']))
        self.assertNotIn('password', res.data)

    def test_user_with_email_exists_error(self):
        """Test error returned if user with email exists."""
        create_user(**self.user_info)
        res = self.client.post(CREATE_USER_URL, self.user_info)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        """Test an error is returned if password is too simple."""
        self.user_info['password'] = 'simple'
        res = self.client.post(CREATE_USER_URL, self.user_info)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=self.user_info['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test generates token for valid credentials."""
        create_user(**self.user_info)

        user_credentials = {
            'email': self.user_info['email'],
            'password': self.user_info['password'],
        }
        res = self.client.post(TOKEN_URL, user_credentials)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credentials(self):
        """Test returns error if credentials invalid."""
        create_user(**self.user_info)

        bad_credentials = {
            'email': 'test@example.com',
            'password': 'wrongpass'
            }
        res = self.client.post(TOKEN_URL, bad_credentials)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
