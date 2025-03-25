from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist
from datetime import *
from django.db.models import Prefetch

from sesar_api.serializers import SampleSerializer
from sesar_api.models import Sample
from sesar_api.util import get_samples, get_team_sesar_codes_with_permission, get_paginated_queryset, generate_sample_jsonld


# get all viewable samples in user team
@api_view(['GET'])
def view_user_team_samples(request, name):
    order_by = '-' if request.GET.get('order', 'asc') == 'desc' else ''
    order_by += request.GET.get('sort', 'igsn')
    offset = int(request.GET.get('offset', 0))
    limit = int(request.GET.get('limit', 50))

    optional_filters = {
        'igsn_prefix': request.GET.get('sesar_code', None),
        'igsn__icontains': request.GET.get('igsn', None),
        'name__icontains': request.GET.get('sample_name', None),
        'registration_date__gt': request.GET.get('date_start', None),
        'registration_date__lt': request.GET.get('date_end', None),
    }
    
    try:
        team = request.user.sesaruser.teams.get(name=name, part_of_team__isnull=True)
    
        if team:
            sesar_codes = get_team_sesar_codes_with_permission(request.user.sesaruser, team, 'view_sample')

            filters = {
                'team_owner': team
            }

            if sesar_codes != 'all':
                filters['igsn_prefix__in'] = sesar_codes

            for key, value in optional_filters.items():
                if value is not None and value != '':
                    filters[key] = value

            samples_queryset = get_samples(filters, order_by)
            total_samples = samples_queryset.count()
            samples = get_paginated_queryset(samples_queryset, offset, limit)

            serializer = SampleSerializer(samples, many=True)
            return Response({
                'total': total_samples,
                'totalNotFiltered': total_samples,
                'rows': serializer.data,
            }, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_igsn_list_for_sitemap(request):
    order_by = 'sample_id'
    limit = int(request.GET.get('limit', 50000))
    offset = int(request.GET.get('page', 0)) * limit
    
    
    values = ['igsn', 'last_update_date']
    try:
        igsns_queryset = get_samples(order_by=order_by, values=values)
        igsns = get_paginated_queryset(igsns_queryset, offset, limit)

        return Response(igsns, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(e, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_sample_jsonld(request):
    igsn = request.GET.get('igsn')

    try:
        sample = Sample.objects.select_related(
            "igsn_prefix",
            "classification",
            "top_level_classification",
            "cur_owner",
            "cur_registrant",
            "sample_type",
            "country",
            "external_parent_sample_type",
            "launch_type",
            "nav_type",
            "origin_sample",
        ).prefetch_related(
            "other_names",
            "publication_urls",
            "sample_docs",
            Prefetch(
                "origin_sample__sample_set", 
                queryset=Sample.objects.all(),
                to_attr="children_samples",
            ),
            Prefetch(
                'sample_set',
                queryset=Sample.objects.all(),
                to_attr="children_samples"
            )
        ).get(igsn=igsn)

        return Response(generate_sample_jsonld(sample), status=status.HTTP_200_OK)
    except Sample.DoesNotExist:
        return Response({'error': 'Sample does not exist'}, status=status.HTTP_404_NOT_FOUND)