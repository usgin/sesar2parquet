from rest_framework import serializers
from sesar_api.models import Initiative, InitiativeType

class InitiativeSerializer(serializers.ModelSerializer):
    initiative_type = serializers.StringRelatedField()

    class Meta:
        model = Initiative
        fields = [
            'label',
            'description',
            'funding',
            'begin_date',
            'end_date',
            'initiative_uri',
            'initiative_type',
        ]
