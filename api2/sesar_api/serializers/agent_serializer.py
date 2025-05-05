from rest_framework import serializers
from sesar_api.models import Individual, Institution, Team
from .individual_serializer import IndividualSerializer
from .institution_serializer import InstitutionSerializer
# from .team_serializer import TeamSerializer TODO

class AgentSerializer(serializers.Serializer):
    def to_representation(self, instance):
        if isinstance(instance, Individual):
            return IndividualSerializer(instance).data
        elif isinstance(instance, Institution):
            return InstitutionSerializer(instance).data
        # elif isinstance(instance, Team):
        #     return TeamSerializer(instance).data
        return None