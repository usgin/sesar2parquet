from rest_framework import serializers
from sesar_api.models import Sample, SampleType, Classification, Country, NavType, LaunchType


class SampleSerializer(serializers.ModelSerializer):
    origin_sample = serializers.SlugRelatedField(queryset=Sample.objects.all(), slug_field='igsn')
    sample_type = serializers.SlugRelatedField(queryset=SampleType.objects.all(), slug_field='name')
    classification = serializers.SlugRelatedField(queryset=Classification.objects.filter(parent_classification__isnull=False), slug_field='name')
    top_level_classification = serializers.SlugRelatedField(queryset=Classification.objects.filter(parent_classification__isnull=True), slug_field='name')
    country = serializers.SlugRelatedField(queryset=Country.objects.filter(is_active=1), slug_field='name')
    nav_type = serializers.SlugRelatedField(queryset=NavType.objects.all(), slug_field='name')
    launch_type = serializers.SlugRelatedField(queryset=LaunchType.objects.all(), slug_field='name')


    class Meta:
        model = Sample
        fields = ['origin_sample', 'sample_type', 'igsn', 'publish_date', 'name', 'current_archive', 'collection_method', 'collection_method_descr', 'size', 'size_unit', 'classification', 'classification_comment', 'top_level_classification', 'description', 'depth_min', 'depth_max', 'depth_scale', 'age_min', 'age_max', 'geological_age', 'geological_unit', 'sample_unit', 'latitude', 'latitude_end', 'longitude', 'longitude_end', 'elevation', 'elevation_end', 'elevation_unit', 'primary_location_type', 'primary_location_name', 'location_description', 'locality', 'locality_description', 'country', 'field_name', 'province', 'county', 'city', 'cruise_field_prgrm', 'platform_type', 'platform_name', 'platform_descr', 'collector', 'collection_start_date', 'collection_end_date', 'collection_date_precision', 'nav_type', 'launch_platform_name', 'launch_type', 'launch_id', 'purpose', 'easting', 'northing', 'zone', 'vertical_datum', 'publish_date']
        read_only_fields = ['origin_sample', 'sample_type', 'igsn', 'publish_date', 'name', 'current_archive', 'collection_method', 'collection_method_descr', 'size', 'size_unit', 'classification', 'classification_comment', 'top_level_classification', 'description', 'depth_min', 'depth_max', 'depth_scale', 'age_min', 'age_max', 'geological_age', 'geological_unit', 'sample_unit', 'latitude', 'latitude_end', 'longitude', 'longitude_end', 'elevation', 'elevation_end', 'elevation_unit', 'primary_location_type', 'primary_location_name', 'location_description', 'locality', 'locality_description', 'country', 'field_name', 'province', 'county', 'city', 'cruise_field_prgrm', 'platform_type', 'platform_name', 'platform_descr', 'collector', 'collection_start_date', 'collection_end_date', 'collection_date_precision', 'nav_type', 'launch_platform_name', 'launch_type', 'launch_id', 'purpose', 'easting', 'northing', 'zone', 'vertical_datum', 'publish_date']