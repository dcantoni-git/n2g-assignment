"""
Views for the message API.
"""
from rest_framework import authentication, permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response

from message.serializers import MessageSerializer
from core import models
from message import serializers
import requests
from requests.exceptions import HTTPError
import pika
import json
import time
import environ


env = environ.Env()
environ.Env.read_env()


def connect_to_rabbitmq():
    rabbitmq_credentials = pika.PlainCredentials(env('EXCHANGE'),env('EXCHANGE_PASS'))  # noqa: E501
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

    def get(self, request, number_of_messages, format=None):
        """Consumes data from the API and send them to RabbitMQ exchange."""

        # Get data from the external API.
        external_api_url = 'https://xqy1konaa2.execute-api.eu-west-1.amazonaws.com/prod/results'  # noqa: E501
        connection, channel = connect_to_rabbitmq()

        for i in range(number_of_messages):
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

            try:
                channel.basic_publish(
                    exchange='cand_upk1',
                    routing_key=routing_key,
                    body=body_json,
                    properties=pika.BasicProperties(content_type='application/json')  # noqa: E501
                    )
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
            time.sleep(0.1)  # Delay between API calls

        channel.close()
        connection.close()

        if number_of_messages == 1:
            publish_msg = {
                'publish_msg': '1 message was sent to the exchange.'
            }
        else:
            publish_msg = {
                'publish_msg': f'{number_of_messages} messages were sent to the exchange.'
            }

        return Response(publish_msg, status.HTTP_200_OK)


class StoreToDatabaseView(APIView):
    """Get the data from the RabbitMQ queue and store them to database."""
    serializer_class = MessageSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, number_of_messages, format=None):
        """Get the data from the RabbitMQ queue and store them to database."""
        connection, channel = connect_to_rabbitmq()
        messages_stored_in_db = 0
        for i in range(number_of_messages):
            try:
                method_frame, header, body = channel.basic_get(queue='cand_upk1_results', auto_ack=True)  # noqa: E501
                if body is not None:
                    body_dict = json.loads(body)
                    routing_key_list = method_frame.routing_key.split('.')
                    user = models.User.objects.get(id=body_dict['user_id'])
                    message = models.Message(
                        user=user,
                        gatewayEui=hex(int(routing_key_list[0]))[2:],
                        profileId='0x' + hex(int(routing_key_list[1]))[2:].zfill(4),  # noqa: E501
                        endpointId='0x' + hex(int(routing_key_list[2]))[2:].zfill(2),  # noqa: E501
                        clusterId='0x' + hex(int(routing_key_list[3]))[2:].zfill(4),  # noqa: E501
                        attributeId='0x' + hex(int(routing_key_list[4]))[2:].zfill(4),  # noqa: E501
                        value=body_dict['value'],
                        timestamp=body_dict['timestamp']
                    )
                    message.save()
                    messages_stored_in_db += 1

                    if messages_stored_in_db == number_of_messages:
                        break
                else:
                    break
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

        channel.close()
        connection.close()
        if messages_stored_in_db == 0:
            db_msg = "There are no messages in the queue."
        elif messages_stored_in_db == 1:
            db_msg = "1 message was stored in the database."
        else:
            db_msg = f'{messages_stored_in_db} message were stored in the database.'  # noqa: E501
        res = {
            'db_msg': db_msg
        }
        return Response(res, status.HTTP_200_OK)


class StoreToDatabaseContinuousView(APIView):
    """Establish a continuous listening to the results queue. NOT RECOMMENDED, FOR DEMO PURPOSES ONLY! It is terminated manually."""  # noqa: E501
    serializer_class = MessageSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        """Get the data from the RabbitMQ queue and store them to database."""
        connection, channel = connect_to_rabbitmq()

        def on_message_callback(ch, method, properties, body):
            # raise pika.exceptions.StopConsuming
            """Callback that handles the message. It stores it to database and then send the ack message for the next message."""  # noqa: E501
            body_dict = json.loads(body)
            routing_key_list = method.routing_key.split('.')
            try:
                user = models.User.objects.get(id=body_dict['user_id'])
                message = models.Message(
                    user=user,
                    gatewayEui=hex(int(routing_key_list[0]))[2:],
                    profileId='0x' + hex(int(routing_key_list[1]))[2:].zfill(4),  # noqa: E501
                    endpointId='0x' + hex(int(routing_key_list[2]))[2:].zfill(2),  # noqa: E501
                    clusterId='0x' + hex(int(routing_key_list[3]))[2:].zfill(4),  # noqa: E501
                    attributeId='0x' + hex(int(routing_key_list[4]))[2:].zfill(4),  # noqa: E501
                    value=body_dict['value'],
                    timestamp=body_dict['timestamp']
                )
                message.save()

                db_msg = 'Message was stored in the database successfully!'
                print(db_msg)

            except Exception as e:
                error_msg = {
                    'db_error_msg': str(e)
                }
                raise error_msg
            ch.basic_ack(delivery_tag=method.delivery_tag)

        try:
            channel.basic_consume(queue='cand_upk1_results', on_message_callback=on_message_callback)  # noqa: E501
            channel.start_consuming()

        except Exception as e:
            error_msg = {
                'error_msg': str(e)
            }
            return Response(error_msg, status.HTTP_400_BAD_REQUEST)
        return Response("Never reaches here!")


class ShowStoredMessagesView(APIView):
    """View for manage showing the stored messages to the user."""
    serializer_class = serializers.MessageSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        """Show the stored messages in paginated format (100 messages per page)."""  # noqa: E501
        queryset = models.Message.objects.filter(user=request.user).order_by('-timestamp')  # noqa: E501
        serializer = self.serializer_class(queryset, many=True)
        paginator = PageNumberPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = self.serializer_class(paginated_queryset, many=True)

        return paginator.get_paginated_response(serializer.data)
