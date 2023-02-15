"""
Views for the message API.
"""
from rest_framework import authentication, permissions, viewsets
from rest_framework.pagination import PageNumberPagination
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
from core import models
# import time
# import re
# import mysql.connector


def connect_to_rabbitmq():
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
        # status_code = re.findall('\d{3}',str(e))[0]
        error_msg = {
            'error_msg': str(e)
        }
        return Response(error_msg, status.HTTP_400_BAD_REQUEST)
    return connection, channel

class SendToExchangeView(APIView):
    """Consumes data from the API and send them to RabbitMQ exchange."""
    serializer_class = MessageSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        """Consumes data from the API and send them to RabbitMQ exchange."""

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

        gatewayEui_dec = int(data['gatewayEui'], 16)
        profileId_dec = int(data['profileId'], 16)
        endpointId_dec = int(data['endpointId'], 16)
        clusterId_dec = int(data['clusterId'], 16)
        attributeId_dec = int(data['attributeId'], 16)

        routing_key = f"{gatewayEui_dec}.{profileId_dec}.{endpointId_dec}.{clusterId_dec}.{attributeId_dec}"  # noqa: E501

        body_dict = {
            'user_id': request.user.id,
            'value': data['value'],
            'timestamp': data['timestamp'],
        }

        body_json = json.dumps(body_dict, indent=4)

        connection, channel = connect_to_rabbitmq()

        try:
            channel.basic_publish(
                exchange='cand_upk1',
                routing_key=routing_key,
                body=body_json,
                properties=pika.BasicProperties(content_type='application/json')  # noqa: E501
                )
            channel.close()
            connection.close()
            publish_msg = 'Message was sent to exchange successfully!!'
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

        return Response(data, status.HTTP_200_OK)


# def store_message_to_database(msg_dict: dict):
#     user_id = msg_dict['user_id']
#     gatewayEui_hex = hex(msg_dict['gatewayEui'])
#     profileId_hex = hex(msg_dict['profileId'])
#     endpointId_hex = int(msg_dict['endpointId'], 16)
#     clusterId_hex = int(msg_dict['clusterId'], 16)
#     attributeId_hex = int(msg_dict['attributeId'], 16)
#     value = msg_dict['user_id']
#     timestamp = msg_dict['timestamp']
#     message = models.Message(
#         user=user_id,
#         gatewayEui=gatewayEui_hex,
#         profileId=profileId_hex,
#         endpointId=endpointId_hex,
#         clusterId=clusterId_hex,
#         attributeId=attributeId_hex,
#         value=value,
#         timestamp=timestamp
#     )
#     message.save()

# def normalize_hex_value(hex_value: str, length: int):
#     norm_hex_value = "0x" + hex_value[2:].zfill(length-2)
#     return norm_hex_value


class StoreToDatabaseView(APIView):
    """Get the data from the RabbitMQ queue and store them to database."""
    serializer_class = MessageSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, time, format=None):
        """Get the data from the RabbitMQ queue and store them to database."""
        connection, channel = connect_to_rabbitmq()
        try:
            method, header, body = channel.basic_get(queue='cand_upk1_results', auto_ack=True)
            channel.close()
            connection.close()
        except ValueError as e:
            error_msg = {
            'value_error': str(e)
            }
            return Response(error_msg, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_msg = {
            'error_msg': str(e)
            }
            return Response(error_msg, status.HTTP_400_BAD_REQUEST)

        if body is not None:
            body_dict = json.loads(body)
            routing_key_list = method.routing_key.split('.')
            data = {
                'gatewayEui': hex(int(routing_key_list[0]))[2:],
                'profileId': '0x' + hex(int(routing_key_list[1]))[2:].zfill(4),
                'endpointId': '0x' + hex(int(routing_key_list[2]))[2:].zfill(2),
                'clusterId': '0x' + hex(int(routing_key_list[3]))[2:].zfill(4),
                'attributeId': '0x' + hex(int(routing_key_list[4]))[2:].zfill(4),
                'value': body_dict['value'],
                'timestamp': body_dict['timestamp']
            }

            try:
                user = models.User.objects.get(id=body_dict['user_id'])
                message = models.Message(
                    user=user,
                    gatewayEui=data['gatewayEui'],
                    profileId=data['profileId'],
                    endpointId=data['endpointId'],
                    clusterId=data['clusterId'],
                    attributeId=data['attributeId'],
                    value=data['value'],
                    timestamp=data['timestamp']
                )
                message.save()

                consume_msg = {
                'consume_msg': 'Message was stored in the database successfully!'
                }
                data.update(consume_msg)
                return Response(data, status.HTTP_200_OK)
            except Exception as e:
                error_msg = {
                    'db_error_msg': str(e)
                }
                return Response(error_msg, status.HTTP_400_BAD_REQUEST)

        else:
            consume_msg = {
                'consume_msg': 'No messages in the queue!'
            }
            return Response(consume_msg, status.HTTP_200_OK)


class ShowStoredMessagesView(APIView):
    """View for manage showing the stored messages to the user."""
    serializer_class = serializers.MessageSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        """Show the stored messages in paginated format (100 messages per page)."""
        queryset = models.Message.objects.filter(user=request.user).order_by('-timestamp')
        serializer = self.serializer_class(queryset, many=True)
        paginator = PageNumberPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = self.serializer_class(paginated_queryset, many=True)

        return paginator.get_paginated_response(serializer.data)
