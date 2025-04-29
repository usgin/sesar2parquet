from rest_framework import serializers
from sesar_api.models import LocationMethod

class LocationMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationMethod
        fields = [
            'label',
            'description',
            'source',
        ]
