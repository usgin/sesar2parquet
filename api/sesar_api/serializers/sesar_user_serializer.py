from rest_framework import serializers
from sesar_api.models import SesarUser


class SesarUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = SesarUser
        fields = ['sesar_user_id', 'lname', 'fname', 'orcid']
        read_only_fields = ['sesar_user_id','lname', 'fname', 'orcid']