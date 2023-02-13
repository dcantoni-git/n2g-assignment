"""
Serializers for the message API.
"""
from rest_framework import serializers

from core.models import Message


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for recipes."""

    class Meta:
        model = Message
        fields = [
            'gatewayEui', 'profileId', 'endpointId',
            'clusterId', 'attributeId', 'value', 'timestamp'
        ]
