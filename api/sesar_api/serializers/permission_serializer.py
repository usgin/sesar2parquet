from django.db.models import fields
from rest_framework import serializers
import re
from sesar_api.models import Permission, Team, TeamMember, SesarUser, SesarUserCode, Sample, SesarRole
from django.contrib.auth.models import Group as AuthGroup
from django.utils import timezone
from datetime import timedelta
 

class PermissionSerializer(serializers.ModelSerializer):
    user_code = serializers.SlugRelatedField(read_only=True,slug_field='user_code')
    sample = serializers.SlugRelatedField(read_only=True,slug_field='igsn')
    sesar_role = serializers.SlugRelatedField(read_only=True,slug_field='sesar_role_name')
    sesar_user = serializers.StringRelatedField()
    team = serializers.StringRelatedField()
    auth_group = serializers.SlugRelatedField(read_only=True,slug_field='name')

    class Meta:
        model = Permission
        fields = ['id', 'user_code', 'sample', 'geopass_id', 'orcid_id', 'sesar_user', 'team', 'sesar_role', 'auth_group', 'activate_date', 'deactivate_date', 'granted_by_team']
        read_only_fields = ['id', 'user_code', 'sample', 'geopass_id', 'orcid_id', 'sesar_user', 'team', 'sesar_role', 'auth_group', 'activate_date', 'deactivate_date', 'granted_by_team']


class PermissionWriteSerializer(serializers.ModelSerializer):
    user_code = serializers.SlugRelatedField(queryset=SesarUserCode.objects.all(), slug_field='user_code', allow_null=True, required=False)
    sample = serializers.SlugRelatedField(queryset=Sample.objects.all(), slug_field='igsn', allow_null=True, required=False)
    sesar_role = serializers.SlugRelatedField(queryset=SesarRole.objects.all(), slug_field='sesar_role_name', allow_null=True, required=False)
    sesar_user = serializers.PrimaryKeyRelatedField(queryset=SesarUser.objects.all(), allow_null=True, required=False)
    team = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all(), allow_null=True, required=False)
    auth_group = serializers.SlugRelatedField(queryset=AuthGroup.objects.all(), slug_field='name')
    granted_by_team = serializers.PrimaryKeyRelatedField(queryset=Team.objects.filter(part_of_team=None), allow_null=True, required=False)

    class Meta:
        model = Permission
        fields = ['user_code', 'sample', 'sesar_user', 'team', 'sesar_role', 'auth_group', 'activate_date', 'deactivate_date', 'granted_by_team']


    def validate_activate_date(self, value):
        if value == None:
            return self.Meta.model._meta.get_field('activate_date').get_default()

        # set today start to yesterday to give a buffer for any timezone descrepancies
        now = timezone.now()
        today_start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

        # Validation: Ensure the value is not before today
        if value < today_start:
            raise serializers.ValidationError(
                f"The activate date ({value}) cannot be in the past.({today_start})"
            )

        return value

    def validate_deactivate_date(self, value):
        activate_date = self.initial_data.get('activate_date')
        if activate_date:
            activate_date = serializers.DateTimeField().to_internal_value(activate_date)
            
            if value and value < activate_date:
                raise serializers.ValidationError("Deactivate date cannot be before activate date.")

        return value