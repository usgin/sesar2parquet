from rest_framework import serializers
from sesar_api.models import RelatedResource

class RelatedResourceSerializer(serializers.ModelSerializer):
    relation_type = serializers.SlugRelatedField(slug_field='label', read_only=True)
    related_sesar_sample = serializers.SlugRelatedField(slug_field='igsn', read_only=True)
    related_resource_type = serializers.SlugRelatedField(slug_field='label', read_only=True)

    class Meta:
        model = RelatedResource
        fields = [
            'relation_id',
            'relation_label',
            'relation_type',
            'related_resource_uri',
            'related_sesar_sample',
            'related_resource_type',
        ]
