from rest_framework import serializers
from sesar_api.models import SesarUserCode, SesarUser, Group
import re


class UserCodeSerializer(serializers.ModelSerializer):
    sesar_user = serializers.SlugRelatedField(queryset=SesarUser.objects.filter(deactivation_date__isnull=True), slug_field='orcid')
    group = serializers.SlugRelatedField(queryset=Group.objects.filter(part_of_group__isnull=True), slug_field='name')
    sample_count = serializers.SerializerMethodField()

    class Meta:
        model = SesarUserCode
        fields = ['sesar_user', 'group', 'user_code', 'doi_prefix', 'sample_count']
        read_only_fields = ['sesar_user', 'group', 'user_code', 'doi_prefix', 'sample_count']

    def get_sample_count(self, obj):
        return obj.samples.count()


class UserCodeWriteSerializer(serializers.ModelSerializer):
    sesar_user = serializers.SlugRelatedField(queryset=SesarUser.objects.filter(deactivation_date__isnull=True), slug_field='orcid', required=False)
    group = serializers.SlugRelatedField(queryset=Group.objects.filter(part_of_group__isnull=True), slug_field='name', required=False)

    class Meta:
        model = SesarUserCode
        fields = ['sesar_user', 'group', 'user_code', 'doi_prefix']

    def validate_user_code(self, value):
        if not re.fullmatch(r'^IE[a-zA-Z0-9]{3}$', value):
            raise serializers.ValidationError("User code must be 5 characters long, alphanumeric, and begin with IE.")
        return value

    def validate(self, data):
        sesar_user = data.get('sesar_user')
        group = data.get('group')

        # Check if user code has an owner
        if sesar_user and group:
            raise serializers.ValidationError("A user code cannot be owned by both a user and a group simultaneously.")
        if not sesar_user and not group:
            raise serializers.ValidationError("User code missing owner.")

        return data