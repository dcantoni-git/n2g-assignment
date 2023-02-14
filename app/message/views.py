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
from requests.exceptions import HTTPError
from rest_framework import status
import pika
import json
# import re
# import mysql.connector


class ConsumeDataView(APIView):
    """Consumes data from the API and send them to RabbitMQ exchange."""
    serializer_class = MessageSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        """Returns a list of APIView features"""

        # Get data from the external API.
        external_api_url = 'https://xqy1konaa2.execute-api.eu-west-1.amazonaws.com/prod/results'  # noqa: E501
        try:
            response = requests.get(external_api_url)
            response.raise_for_status()
            data = response.json()
        except HTTPError as e:
            return Response(f'HTTPError: {e}', response.status_code)
        except Exception as e:
            return Response(f'Error: {e}', response.status_code)

        # Connect to RabbitMQ Exchange.
        rabbitmq_credentials = pika.PlainCredentials('cand_upk1', 'E66YEUd7b0lozdzd')  # noqa: E501
        rabbitmq_params = pika.ConnectionParameters(
            host='candidatemq.n2g-dev.net',
            credentials=rabbitmq_credentials
            )
        try:
            connection = pika.BlockingConnection(rabbitmq_params)
            channel = connection.channel()
            channel.confirm_delivery()
        except Exception as e:
            # Regular Expression to find the status code.
            # Not included! Uncertain that exists in every exception message
            # status_code = re.findall('\d{3}',str(e))
            error_msg = {
                'error_msg': str(e)
            }
            return Response(error_msg, status.HTTP_400_BAD_REQUEST)

        gatewayEui_dec = int(data['gatewayEui'], 16)
        profileId_dec = int(data['profileId'], 16)
        endpointId_dec = int(data['endpointId'], 16)
        clusterId_dec = int(data['clusterId'], 16)
        attributeId_dec = int(data['attributeId'], 16)

        routing_key = f"{gatewayEui_dec}.{profileId_dec}.{endpointId_dec}.{clusterId_dec}.{attributeId_dec}"  # noqa: E501

        body_dict = {
            'user': request.user.id,
            'value': data['value'],
            'timestamp': data['timestamp'],
        }

        body_json = json.dumps(body_dict, indent=4)

        try:
            channel.basic_publish(
                exchange='cand_upk1',
                routing_key=routing_key,
                body=body_json,
                properties=pika.BasicProperties(content_type='application/json')  # noqa: E501
                )
            publish_msg = 'Message publish was confirmed'
        except pika.exceptions.UnroutableError as e:
            error_msg = {
                'error_msg': f"Message publish failed! (gatewayEui: {data['gatewayEui']})",  # noqa: E501
                'unroutable_error': str(e)
            }
            return Response(error_msg, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_msg = {
                'error_msg': f"Message publish failed! (gatewayEui: {data['gatewayEui']})",  # noqa: E501
                'details': str(e)
            }
            return Response(error_msg, status.HTTP_400_BAD_REQUEST)

        data.update({'publish_msg': publish_msg})
        return Response(data, response.status_code)


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
