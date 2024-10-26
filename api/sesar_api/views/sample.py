from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist
from datetime import *

from sesar_api.serializers import SampleSerializer
from sesar_api.util import get_samples, get_group_user_codes_with_permission


# get all viewable samples in user group
@api_view(['GET'])
def view_user_group_samples(request, name):
    order_by = '-' if request.GET.get('order') == 'desc' else ''
    order_by += request.GET.get('sort', 'igsn')
    offset = int(request.GET.get('offset', 0))
    limit = int(request.GET.get('limit', 25))

    optional_filters = {
        'igsn_prefix': request.GET.get('user_code', None),
        'igsn__icontains': request.GET.get('igsn', None),
        'name__icontains': request.GET.get('sample_name', None),
        'registration_date__gt': request.GET.get('date_start', None),
        'registration_date__lt': request.GET.get('date_end', None),
    }
    
    try:
        group = request.user.sesaruser.groups.get(name=name, part_of_group__isnull=True)
    
        if group:
            user_codes = get_group_user_codes_with_permission(request.user.sesaruser, group, 'view_sample')

            filters = {
                'igsn_prefix__in': user_codes,
                'group_owner': group,
                'group_owner': group
            }

            for key, value in optional_filters.items():
                if value is not None and value != '':
                    filters[key] = value

            total_samples = get_samples(filters, None, None, None)
            samples = get_samples(filters, order_by, offset, limit)

            serializer = SampleSerializer(samples, many=True)
            return Response({
                'total': total_samples.count(),
                'totalNotFiltered': total_samples.count(),
                'rows': serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)