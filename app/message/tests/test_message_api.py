"""
Tests for the message API.
"""
from django.test import TestCase
# from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CONSUME_DATA_URL = reverse('message:consume_data')
STORE_DATA_URL = reverse('message:store_data')
SHOW_DATA_URL = reverse('message:show_data')


class PublicRecipeAPITests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    # def test_auth_required_consume_data(self):
    #     """Test auth is required to consume data."""
    #     res = self.client.get(CONSUME_DATA_URL)

    #     self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    # def test_auth_required_store_data(self):
    #     """Test auth is required to store data."""
    #     res = self.client.get(STORE_DATA_URL)

    #     self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_auth_required_show_data(self):
        """Test auth is required to show data.."""
        res = self.client.get(SHOW_DATA_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

# ΝΑ ΤΟ ΑΛΛΑΞΩ!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# class PrivateRecipeApiTests(TestCase):
#     """Test authenticated API requests."""

#     def setUp(self):
#         self.client = APIClient()
#         self.user = get_user_model().objects.create_user(
#             'user@example.com',
#             'testpass123',
#         )
#         self.client.force_authenticate(self.user)

#     def test_retrieve_recipes(self):
#         """Test retrieving a list of recipes."""
#         create_recipe(user=self.user)
#         create_recipe(user=self.user)

#         res = self.client.get(RECIPES_URL)

#         recipes = Recipe.objects.all().order_by('-id')
#         serializer = RecipeSerializer(recipes, many=True)
#         self.assertEqual(res.status_code, status.HTTP_200_OK)
#         self.assertEqual(res.data, serializer.data)

#     def test_recipe_list_limited_to_user(self):
#         """Test list of recipes is limited to authenticated user."""
#         other_user = get_user_model().objects.create_user(
#             'other@example.com',
#             'password123',
#         )
#         create_recipe(user=other_user)
#         create_recipe(user=self.user)

#         res = self.client.get(RECIPES_URL)

#         recipes = Recipe.objects.filter(user=self.user)
#         serializer = RecipeSerializer(recipes, many=True)
#         self.assertEqual(res.status_code, status.HTTP_200_OK)
#         self.assertEqual(res.data, serializer.data)
