from django.db.models import fields
from rest_framework import serializers
import re
from sesar_api.models import Team, TeamMember, SesarUser
from django.contrib.auth.models import Group as AuthGroup
from .sesar_user_serializer import SesarUserSerializer


class MemberSerializer(serializers.ModelSerializer):
    team = serializers.StringRelatedField(read_only=True)
    auth_group = serializers.StringRelatedField(read_only=True)
    sesar_user = SesarUserSerializer(read_only=True)
    class Meta:
        model = TeamMember
        fields = ['id', 'team', 'sesar_user', 'auth_group', 'join_date', 'status']
        read_only_fields = ['id', 'team', 'sesar_user', 'auth_group', 'join_date', 'status']


class TeamSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(read_only=True)
    members = SesarUserSerializer(many=True, read_only=True)
    class Meta:
        model = Team
        fields = ['id', 'owner', 'name', 'display_name', 'description', 'doi_prefix', 'contact_email', 'members']
        read_only_fields = ['id', 'name', 'display_name', 'description', 'doi_prefix', 'contact_email', 'members']


class TeamWriteSerializer(serializers.ModelSerializer):
    owner = serializers.SlugRelatedField(queryset=SesarUser.objects.filter(deactivation_date=None),slug_field='orcid')
    contact_email = serializers.EmailField(required=True, allow_blank=False)
    class Meta:
        model = Team
        fields = ['owner', 'name', 'display_name', 'description', 'activate_date', 'deactivate_date', 'doi_prefix', 'contact_email']
        read_only_fields = ['activate_date', 'doi_prefix']

    def create(self, validated_data):
        return Team.objects.create(**validated_data)

    def validate_name(self, value):
        """
        Check that the name contains valid characters.
        """
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_\.-]+[A-Za-z0-9]", value):
            raise serializers.ValidationError("Name can only contain letters (A-Z), numbers (0-9), underscores (_), periods (.), and hyphens (-).")
        return value


class SubTeamWriteSerializer(serializers.ModelSerializer):
    part_of_team = serializers.PrimaryKeyRelatedField(queryset=Team.objects.filter(part_of_team=None))
    class Meta:
        model = Team
        fields = ['id', 'part_of_team', 'name', 'display_name', 'description', 'activate_date', 'deactivate_date',]

    def create(self, validated_data):
        return Team.objects.create(**validated_data)

    def validate_name(self, value):
        """
        Check that the name contains valid characters.
        """
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_\.-]+[A-Za-z0-9]", value):
            raise serializers.ValidationError("Name can only contain letters (A-Z), numbers (0-9), underscores (_), periods (.), and hyphens (-).")
        return value


class MemberWriteSerializer(MemberSerializer):
    team = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all())
    sesar_user = serializers.PrimaryKeyRelatedField(queryset=SesarUser.objects.filter(deactivation_date=None))
    auth_group = serializers.SlugRelatedField(queryset=AuthGroup.objects.all(), required=False, slug_field='name')
    class Meta:
        model = TeamMember
        fields = ['team', 'sesar_user', 'auth_group', 'join_date', 'status']
        read_only_fields = ['join_date']

    def create(self, validated_data):
        return TeamMember.objects.create(**validated_data)


class SubTeamSerializer(serializers.ModelSerializer):
    part_of_team = TeamSerializer(read_only=True)
    members = SesarUserSerializer(many=True, read_only=True)
    class Meta:
        model = Team
        fields = ['id', 'part_of_team', 'name', 'display_name', 'description', 'activate_date', 'deactivate_date', 'members']
        read_only_fields = ['id', 'activate_date', 'deactivate_date']