from rest_framework import serializers
from sesar_api.models import SamplingMethod

class SamplingMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = SamplingMethod
        fields = [
            'label',
            'description',
            'method_uri',
            'source',
            'scheme_uri',
        ]
