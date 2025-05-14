from rest_framework import serializers
from sesar_api.models import SamplePublicationUrl

class SamplePublicationUrlSerializer(serializers.ModelSerializer):
    class Meta:
        model = SamplePublicationUrl
        fields = [
            'url',
            'description',
            'url_type',
        ]
