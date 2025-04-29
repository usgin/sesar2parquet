from rest_framework import serializers
from sesar_api.models import Sample, SampleType, MaterialType
from .material_type_serializer import MaterialTypeSerializer
from .geologic_time_scale_serializer import GeologicTimeScaleSerializer
from .sesar_spatial_ref_sys_serializer import SesarSpatialRefSysSerializer
from .location_method_serializer import LocationMethodSerializer
from .sampled_feature_type_serializer import SampledFeatureTypeSerializer
from .locality_serializer import LocalitySerializer
from .sampling_method_serializer import SamplingMethodSerializer
from .initiative_serializer import InitiativeSerializer
from .individual_serializer import IndividualSerializer
from .institution_serializer import InstitutionSerializer
from .platform_serializer import PlatformSerializer
from .sesar_user_serializer import SesarUserSerializer


class SampleSerializer(serializers.ModelSerializer):
    sesar_code = serializers.SlugRelatedField(slug_field='sesar_code', read_only=True)
    parent_sample = serializers.SlugRelatedField(queryset=Sample.objects.all(), slug_field='igsn')
    sample_type = serializers.SlugRelatedField(queryset=SampleType.objects.all(), slug_field='label')
    cur_registrant = SesarUserSerializer()
    general_material_type = MaterialTypeSerializer()
    sample_material = MaterialTypeSerializer(many=True)
    geologic_age_younger = GeologicTimeScaleSerializer()
    geologic_age_older = GeologicTimeScaleSerializer()
    depth_spatial_ref = SesarSpatialRefSysSerializer()
    location_method = LocationMethodSerializer()
    sampled_feature_type = SampledFeatureTypeSerializer()
    locality = LocalitySerializer()
    collection_method = SamplingMethodSerializer()
    cruise_field_prgrm = InitiativeSerializer()
    individual_collector = IndividualSerializer()
    institution_collector = InstitutionSerializer()
    platform = PlatformSerializer()
    launch_platform = PlatformSerializer()
    children_igsns = serializers.SerializerMethodField()
    sibling_igsns = serializers.SerializerMethodField()

    class Meta:
        model = Sample
        fields = ['igsn', 'name', 'sesar_code', 'parent_sample', 'sample_type',  'publish_date', 'last_update_date', 'size', 'general_material_type', 'sample_material', 'material_name_verbatim', 'sample_description', 'purpose', 'geologic_age_verbatim', 'numeric_age_min', 'numeric_age_max', 'numeric_age_unit','geologic_age_younger', 'geologic_age_older', 'geologic_unit', 'age_qualifier', 'latitude', 'longitude', 'latitude_end', 'longitude_end', 'depth_min', 'depth_max', 'depth_uom', 'depth_spatial_ref', 'elevation', 'elevation_uom', 'location_method', 'location_qualifier', 'sampled_feature_type', 'locality', 'locality_label', 'locality_detail', 'collection_method', 'collection_method_detail', 'cruise_field_prgrm', 'individual_collector', 'institution_collector', 'platform', 'launch_platform', 'launch_label', 'collection_start_date', 'collection_end_date', 'collection_date_precision', 'cur_registrant', 'children_igsns', 'sibling_igsns']
        read_only_fields = ['igsn', 'name', 'sesar_code', 'parent_sample', 'sample_type',  'publish_date', 'last_update_date', 'size', 'general_material_type', 'sample_material', 'material_name_verbatim', 'sample_description', 'purpose', 'geologic_age_verbatim', 'numeric_age_min', 'numeric_age_max', 'numeric_age_unit','geologic_age_younger', 'geologic_age_older', 'geologic_unit', 'age_qualifier', 'latitude', 'longitude', 'latitude_end', 'longitude_end', 'depth_min', 'depth_max', 'depth_uom', 'depth_spatial_ref', 'elevation', 'elevation_uom', 'location_method', 'location_qualifier', 'sampled_feature_type', 'locality', 'locality_label', 'locality_detail', 'collection_method', 'collection_method_detail', 'cruise_field_prgrm', 'individual_collector', 'institution_collector', 'platform', 'launch_platform', 'launch_label', 'collection_start_date', 'collection_end_date', 'collection_date_precision', 'cur_registrant', 'children_igsns', 'sibling_igsns']

    def get_children_igsns(self, obj):
        # `children_samples` was populated by prefetch
        return [child.igsn for child in getattr(obj, 'children_samples', [])]

    def get_sibling_igsns(self, obj):
        # `sibling_samples` is attached to the parent
        siblings = getattr(getattr(obj, 'parent_sample', None), 'sibling_samples', [])
        return [sibling.igsn for sibling in siblings if sibling.pk != obj.pk]