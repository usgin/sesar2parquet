from rest_framework import serializers
from sesar_api.models import Individual, Institution, Affiliation
from .affiliation_serializer import AffiliationSerializer

class IndividualSerializer(serializers.ModelSerializer):
    affiliations = AffiliationSerializer(many=True, read_only=True)

    class Meta:
        model = Individual
        fields = [
            'label', 'fname', 'lname', 'alt_label', 'description', 'address',
            'email', 'phone', 'fax', 'affiliation', 'individual_uri', 'affiliations'
        ]

    def get_affiliation(self, obj):
        return [str(inst) for inst in obj.affiliations_list]
