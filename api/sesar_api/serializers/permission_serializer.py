from django.db.models import fields
from rest_framework import serializers
import re
from sesar_api.models import Permission, Group, GroupMember, SesarUser, SesarUserCode, Sample, SesarRole
from django.contrib.auth.models import Group as AuthGroup
 

class PermissionSerializer(serializers.ModelSerializer):
    user_code = serializers.SlugRelatedField(read_only=True,slug_field='user_code')
    sample = serializers.SlugRelatedField(read_only=True,slug_field='igsn')
    sesar_role = serializers.SlugRelatedField(read_only=True,slug_field='sesar_role_name')
    sesar_user = serializers.StringRelatedField()
    group = serializers.StringRelatedField()
    auth_group = serializers.SlugRelatedField(read_only=True,slug_field='name')

    class Meta:
        model = Permission
        fields = ['user_code', 'sample', 'geopass_id', 'orcid_id', 'sesar_user', 'group', 'sesar_role', 'auth_group', 'activate_date', 'deactivate_date', 'granted_by_group']
        read_only_fields = ['user_code', 'sample', 'geopass_id', 'orcid_id', 'sesar_user', 'group', 'sesar_role', 'auth_group', 'activate_date', 'deactivate_date', 'granted_by_group']


class PermissionWriteSerializer(serializers.ModelSerializer):
    user_code = serializers.SlugRelatedField(queryset=SesarUserCode.objects.all(), slug_field='user_code', allow_null=True)
    sample = serializers.SlugRelatedField(queryset=Sample.objects.all(), slug_field='igsn', allow_null=True)
    sesar_role = serializers.SlugRelatedField(queryset=SesarRole.objects.all(), slug_field='sesar_role_name', allow_null=True)
    sesar_user = serializers.PrimaryKeyRelatedField(queryset=SesarUser.objects.all(), allow_null=True)
    group = serializers.SlugRelatedField(queryset=Group.objects.all(), slug_field='name', allow_null=True)
    auth_group = serializers.SlugRelatedField(queryset=AuthGroup.objects.all(), slug_field='name')
    granted_by_group = serializers.SlugRelatedField(queryset=Group.objects.filter(part_of_group=None), slug_field='name', allow_null=True)

    class Meta:
        model = Permission
        fields = ['user_code', 'sample', 'geopass_id', 'orcid_id', 'sesar_user', 'group', 'sesar_role', 'auth_group', 'activate_date', 'deactivate_date', 'granted_by_group']