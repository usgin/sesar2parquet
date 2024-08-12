from django.db.models import fields
from rest_framework import serializers
from sesar_api.models import Organization, OrganizationTeam, OrganizationMember, OrganizationTeamMember, SesarUser
 

class OrganizationSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(read_only=True)
    members = serializers.StringRelatedField(many=True, read_only=True)
    class Meta:
        model = Organization
        fields = ['owner', 'name', 'description', 'doi_prefix', 'members']
        read_only_fields = ['doi_prefix']


class OrganizationWriteSerializer(OrganizationSerializer):
    owner = serializers.PrimaryKeyRelatedField(queryset=SesarUser.objects.filter(deactivation_date=None))
    class Meta:
        model = Organization
        fields = ['owner', 'name', 'description', 'activate_date', 'deactivate_date', 'doi_prefix']
        read_only_fields = ['activate_date', 'doi_prefix']
    
    def create(self, validated_data):
        return Organization.objects.create(**validated_data)


class TeamSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(read_only=True)
    class Meta:
        model = OrganizationTeam
        fields = ['organization', 'name', 'description', 'activate_date', 'deactivate_date']
        read_only_fields = ['activate_date', 'deactivate_date']


class MemberSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(read_only=True)
    teams = TeamSerializer(many=True, read_only=True, allow_null=True)
    class Meta:
        model = OrganizationMember
        fields = ['organization', 'sesar_user', 'is_admin', 'join_date', 'teams']
        read_only_fields = ['is_admin', 'join_date']


class MemberWriteSerializer(MemberSerializer):
    organization = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.all())
    class Meta:
        model = OrganizationMember
        fields = ['organization', 'sesar_user', 'is_admin', 'join_date']
        read_only_fields = ['join_date']

    def create(self, validated_data):

        return OrganizationMember.objects.create(**validated_data)


class TeamMemberSerializer(serializers.ModelSerializer):
    team = TeamSerializer(read_only=True)
    member = MemberSerializer(read_only=True)
    class Meta:
        model = OrganizationTeamMember
        fields = ['member', 'team']