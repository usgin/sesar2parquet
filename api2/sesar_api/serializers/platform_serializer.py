from rest_framework import serializers
from sesar_api.models import Platform, PlatformType, LaunchType, Institution

class PlatformSerializer(serializers.ModelSerializer):
    platform_type = serializers.StringRelatedField(required=False)
    launch_type = serializers.StringRelatedField(required=False)
    operator = serializers.StringRelatedField(required=False)

    class Meta:
        model = Platform
        fields = [
            'label',
            'description',
            'platform_type',
            'host_platform_id',
            'launch_type',
            'operator',
            'date_commissioned',
        ]
