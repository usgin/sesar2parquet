from rest_framework import serializers
from sesar_api.models import SampledFeatureType

class SampledFeatureTypeSerializer(serializers.ModelSerializer):
    parent_feature_type = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = SampledFeatureType
        fields = [
            'label',
            'description',
            'feature_type_uri',
            'parent_feature_type',
            'source',
            'scheme_uri',
        ]
