from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Prefetch
from django.utils import timezone

from sesar_api.serializers import SampleLandingPageSerializer
from sesar_api.models import Sample, SampleMaterial

@api_view(['GET'])
@permission_classes([AllowAny])
def get_sample_by_igsn(request):
    igsn = request.GET.get('igsn')
    try:
        sample = (Sample.objects
        .select_related(
            'sesar_code',
            'parent_sample',
            'sample_type',
            'cur_registrant',
            'general_material_type',
            'geologic_age_younger',
            'geologic_age_older',
            'depth_spatial_ref',
            'location_method',
            'sampled_feature_type',
            'locality',
            'collection_method',
            'cruise_field_prgrm',
            'platform',
            'launch_platform'
        ).prefetch_related(
            'other_names',
            'publication_urls',
            'sample_docs',
            Prefetch(
                'parent_sample__sample_set', 
                queryset=Sample.objects.all(),
                to_attr='sibling_samples',
            ),
            Prefetch(
                'sample_set',
                queryset=Sample.objects.all(),
                to_attr='children_samples'
            ),
            Prefetch(
                'samplematerial_set',
                queryset=SampleMaterial.objects.select_related('material_type'),
                to_attr='sample_materials'
            )
        ).get(igsn=igsn))

        # if sample is private
        if sample.publish_date and sample.publish_date > timezone.now():
            return Response({'error': 'Sample is private'}, status=status.HTTP_403_FORBIDDEN)

        # if sample is deactivated
        if sample.archive_date and sample.archive_date < timezone.now():
            return Response({'error': 'Sample is deactivated'}, status=status.HTTP_410_GONE)

        serializer = SampleLandingPageSerializer(sample)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Sample.DoesNotExist:
        return Response({'error': 'Sample does not exist'}, status=status.HTTP_404_NOT_FOUND)