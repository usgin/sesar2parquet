from django.db.models import fields
from rest_framework import serializers
import re
from sesar_api.models import Group, GroupMember, SesarUser
 

class GroupSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = Group
        fields = ['owner', 'name', 'description', 'doi_prefix', 'contact_email']
        read_only_fields = ['name', 'description', 'doi_prefix', 'contact_email']


class GroupWriteSerializer(serializers.ModelSerializer):
    owner = serializers.SlugRelatedField(queryset=SesarUser.objects.filter(deactivation_date=None),slug_field='orcid')
    class Meta:
        model = Group
        fields = ['owner', 'name', 'description', 'activate_date', 'deactivate_date', 'doi_prefix', 'contact_email']
        read_only_fields = ['activate_date', 'doi_prefix']
        extra_kwargs = {'contact_email': {'required': True,
                                  'allow_blank': False}}

    def create(self, validated_data):
        return Group.objects.create(**validated_data)

    def validate_name(self, value):
        """
        Check that the name contains valid characters.
        """
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_\.-]+[A-Za-z0-9]", value):
            raise serializers.ValidationError("Name can only contain letters (A-Z), numbers (0-9), underscores (_), periods (.), and hyphens (-).")
        return value


class TeamWriteSerializer(serializers.ModelSerializer):
    part_of_group = serializers.PrimaryKeyRelatedField(queryset=Group.objects.filter(part_of_group=None))
    class Meta:
        model = Group
        fields = ['part_of_group', 'name', 'description', 'activate_date', 'deactivate_date',]


class MemberSerializer(serializers.ModelSerializer):
    group = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all())
    class Meta:
        model = GroupMember
        fields = ['group', 'sesar_user', 'is_admin', 'join_date']
        read_only_fields = ['is_admin', 'join_date']


class MemberWriteSerializer(MemberSerializer):
    group = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all())
    sesar_user = serializers.PrimaryKeyRelatedField(queryset=SesarUser.objects.filter(deactivation_date=None))
    class Meta:
        model = GroupMember
        fields = ['group', 'sesar_user', 'is_admin', 'join_date']
        read_only_fields = ['join_date']

    def create(self, validated_data):
        return GroupMember.objects.create(**validated_data)


class TeamSerializer(serializers.ModelSerializer):
    part_of_group = serializers.PrimaryKeyRelatedField(read_only=True)
    members = serializers.StringRelatedField(many=True, read_only=True, allow_null=True)
    class Meta:
        model = Group
        fields = ['part_of_group', 'name', 'description', 'activate_date', 'deactivate_date', 'members']
        read_only_fields = ['activate_date', 'deactivate_date']