from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import F, Q, Count

from sesar_api.models import Sample

@api_view(['GET'])
@permission_classes([AllowAny])
def get_published_sample_count(request):
    try:
        count = Sample.objects.filter(
            Q(publish_date__lt=timezone.now()) & 
            (Q(archive_date__isnull=True) | Q(archive_date__lt=timezone.now()))
            ).count()

        return Response(count, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(e, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_published_parent_sample_count(request):
    try:
        count = Sample.objects.filter(
            Q(origin_sample__isnull=True) & 
            Q(publish_date__lt=timezone.now()) & 
            (Q(archive_date__isnull=True) | Q(archive_date__lt=timezone.now()))
            ).count()

        return Response(count, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(e, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_sample_count_by_sample_type(request):
    try:
        results = (Sample.objects
        .filter(
            (Q(archive_date__isnull=True) | Q(archive_date__lt=timezone.now()))
        )
        .values('sample_type__name')
        .annotate(count=Count('sample_id'))
        .order_by('-count')
        )

        return Response(results, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(e, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_sample_count_by_institution(request):
    try:
        results = (Sample.objects
        .filter(
            (Q(archive_date__isnull=True) | Q(archive_date__lt=timezone.now())),
            cur_owner__institution__isnull=False
        )
        .values(institution=F('cur_owner__institution'))
        .annotate(count=Count('sample_id'))
        .order_by('-count')
        )

        return Response(results, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(e, status=status.HTTP_500_INTERNAL_SERVER_ERROR)