from rest_framework import serializers
from sesar_api.models import TransferHistory, SesarUser, Team


class TransferSerializer(serializers.ModelSerializer):
    transfer_by = serializers.StringRelatedField()
    class Meta:
        model = TransferHistory
        fields = ['id', 'transfer_by', 'transfer_time', 'orig_user', 'orig_team', 'data', 'new_user', 'new_team', 'status']
        read_only_fields = ['id', 'transfer_by', 'transfer_time', 'orig_user', 'orig_team', 'data', 'new_user', 'new_team', 'status']


class TransferWriteSerializer(serializers.ModelSerializer):
    transfer_by = serializers.PrimaryKeyRelatedField(queryset=SesarUser.objects.all())
    orig_user = serializers.SlugRelatedField(queryset=SesarUser.objects.all(), slug_field='orcid', required=False, allow_null=True)
    new_user = serializers.SlugRelatedField(queryset=SesarUser.objects.all(), slug_field='orcid', required=False, allow_null=True)
    orig_team = serializers.SlugRelatedField(queryset=Team.objects.filter(part_of_team__isnull=True), slug_field='name', required=False, allow_null=True)
    new_team = serializers.SlugRelatedField(queryset=Team.objects.filter(part_of_team__isnull=True), slug_field='name', required=False, allow_null=True)

    class Meta:
        model = TransferHistory
        fields = ['transfer_by', 'orig_user', 'orig_team', 'data', 'new_user', 'new_team', 'status']
