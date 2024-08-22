from django.db.models import fields
from rest_framework import serializers
import re
from sesar_api.models import Organization, OrganizationTeam, OrganizationMember, OrganizationTeamMember, SesarUser
 

class OrganizationSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = Organization
        fields = ['owner', 'name', 'description', 'doi_prefix']
        read_only_fields = ['name', 'description', 'doi_prefix']


class OrganizationWriteSerializer(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(queryset=SesarUser.objects.filter(deactivation_date=None))
    class Meta:
        model = Organization
        fields = ['owner', 'name', 'description', 'create_date', 'deactivate_date', 'doi_prefix']
        read_only_fields = ['create_date', 'doi_prefix']

    def create(self, validated_data):
        return Organization.objects.create(**validated_data)

    def validate_name(self, value):
        """
        Check that the name contains valid characters.
        """
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_\.-]+[A-Za-z0-9]", value):
            raise serializers.ValidationError("Organization name contains invalid characters.")
        return value


class TeamWriteSerializer(serializers.ModelSerializer):
    organization = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.all())
    members = serializers.PrimaryKeyRelatedField(many=True, queryset=OrganizationMember.objects.all())
    class Meta:
        model = OrganizationTeam
        fields = ['organization', 'name', 'description', 'activate_date', 'deactivate_date', 'members']


class MemberSerializer(serializers.ModelSerializer):
    organization = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.all())
    teams = serializers.StringRelatedField(many=True, read_only=True)
    class Meta:
        model = OrganizationMember
        fields = ['organization', 'sesar_user', 'is_admin', 'join_date', 'teams']
        read_only_fields = ['is_admin', 'join_date']


class MemberWriteSerializer(MemberSerializer):
    organization = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.all())
    sesar_user = serializers.PrimaryKeyRelatedField(queryset=SesarUser.objects.filter(deactivation_date=None))
    class Meta:
        model = OrganizationMember
        fields = ['organization', 'sesar_user', 'is_admin', 'join_date']
        read_only_fields = ['join_date']

    def create(self, validated_data):
        return OrganizationMember.objects.create(**validated_data)


class TeamSerializer(serializers.ModelSerializer):
    organization = serializers.PrimaryKeyRelatedField(read_only=True)
    members = MemberSerializer(many=True, read_only=True, allow_null=True)
    class Meta:
        model = OrganizationTeam
        fields = ['organization', 'name', 'description', 'activate_date', 'deactivate_date', 'members']
        read_only_fields = ['activate_date', 'deactivate_date']