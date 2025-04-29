from rest_framework import serializers
from sesar_api.models import Affiliation, AffiliationType
from .institution_serializer import InstitutionSerializer


class AffiliationSerializer(serializers.ModelSerializer):
    institution = InstitutionSerializer()
    relation_type = serializers.StringRelatedField()

    class Meta:
        model = Affiliation
        fields = [
            'institution',
            'label',
            'description',
            'relation_type',
            'activate_date',
            'deactivate_date',
            'email',
            'address',
        ]
