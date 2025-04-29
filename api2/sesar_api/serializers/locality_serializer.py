from rest_framework import serializers
from sesar_api.models import Locality, SampledFeatureType, Country
from .sampled_feature_type_serializer import SampledFeatureTypeSerializer

class LocalitySerializer(serializers.ModelSerializer):
    feature_type = SampledFeatureTypeSerializer(read_only=True)
    country = serializers.StringRelatedField(read_only=True)
    contained_in = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Locality
        fields = [
            'name',
            'description',
            'feature_type',
            'locality_uri',
            'country',
            'province',
            'county',
            'city',
            'permit',
            'collection_policy',
            'contained_in',
        ]
