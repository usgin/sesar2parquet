from rest_framework import serializers
from sesar_api.models import SesarUser, Individual, Institution
from .individual_serializer import IndividualSerializer
from .institution_serializer import InstitutionSerializer

class SesarUserSerializer(serializers.ModelSerializer):
    individual = IndividualSerializer(read_only=True)
    institution = InstitutionSerializer(read_only=True)

    class Meta:
        model = SesarUser
        fields = [
            'individual',
            'institution',
            'email',
            'registration_date',
            'orcid',
            'doi_prefix',
            'last_login',
        ]
