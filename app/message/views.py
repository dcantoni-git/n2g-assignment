"""
Views for the message API.
"""
from rest_framework import generics, authentication, permissions
# , status
# from rest_framework.authtoken.views import ObtainAuthToken
# from rest_framework.settings import api_settings
from message.serializers import MessageSerializer
# from rest_framework import viewsets
from core.models import Message
from message import serializers

from rest_framework.views import APIView
from rest_framework.response import Response

import requests
# import pika
# import mysql.connector


class ConsumeDataView(APIView):
    """Consumes data from the API and send them to RabbitMQ exchange."""
    serializer_class = MessageSerializer

    def get(self, request, format=None):
        """Returns a list of APIView features"""

        # Get data from the external API.
        external_api_url = 'https://xqy1konaa2.execute-api.eu-west-1.amazonaws'
        try:
            response = requests.get(external_api_url+'.com/prod/results')
            response.raise_for_status()
            data = response.json()
            return Response(data)
        except Exception as err:
            return Response('Other error occurred: {0}'.format(err))


class StoreDataView(generics.CreateAPIView):
    """Create a new user in the system."""
    serializer_class = MessageSerializer


class ShowDataView(generics.CreateAPIView):
    """View for manage showing the stored messages to the user."""
    serializer_class = serializers.MessageSerializer
    queryset = Message.objects.all()
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Retrieve messages for authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by('-id')
