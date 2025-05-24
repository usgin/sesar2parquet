from rest_framework import serializers
from sesar_api.models import SampleDoc

class SampleDocSerializer(serializers.ModelSerializer):
    class Meta:
        model = SampleDoc
        fields = [
            'file_name',
            'file_type',
            'path_to_file'
        ]
