from rest_framework import serializers
from sesar_api.models import SesarSpatialRefSys

class SesarSpatialRefSysSerializer(serializers.ModelSerializer):
    class Meta:
        model = SesarSpatialRefSys
        fields = [
            'name',
            'description',
            'identifier',
        ]
