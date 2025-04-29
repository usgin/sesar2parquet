from rest_framework import serializers
from sesar_api.models import Institution, InstitutionType

class InstitutionSerializer(serializers.ModelSerializer):
    institution_type = serializers.StringRelatedField()

    class Meta:
        model = Institution
        fields = [
            'institution_type',
            'label',
            'alt_label',
            'description',
            'email',
            'address',
        ]
