from rest_framework import serializers
from sesar_api.models import MaterialType

class MaterialTypeSerializer(serializers.ModelSerializer):
    parent_material_type = serializers.SerializerMethodField()

    class Meta:
        model = MaterialType
        fields = [
            'label',
            'description',
            'material_type_uri',
            'parent_material_type',
            'source',
            'scheme_uri',
        ]

    def get_parent_material_type(self, obj):
        if obj.parent_material_type:
            return MaterialTypeSerializer(obj.parent_material_type).data
        return None
