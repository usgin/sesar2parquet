from rest_framework import serializers
from sesar_api.models import GeologicTimeScale

class GeologicTimeScaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeologicTimeScale
        fields = [
            'label',
            'description',
            'geologic_time_interval_uri',
            'source',
            'scheme_uri',
            'numeric_older_bound',
            'numeric_younger_bound',
            'notation',
        ]
