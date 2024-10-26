from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db.models import Q
import os
import json

from sesar_api.serializers import TransferSerializer, TransferWriteSerializer
from sesar_api.permissions import CanTransferGroupSample
from sesar_api.models import TransferHistory, Sample, Group

from sesar_api.util import get_samples


# get all transfers
@api_view(['GET'])
def view_transfers(request):
    try:
        # get group transfers
        if request.GET.get('group', False):
            group = Group.objects.get(name=request.GET.get('group'), part_of_group__isnull=True)
            if CanTransferGroupSample().has_object_permission(request, None, group):
                transfers = TransferHistory.objects.filter(Q(new_group=group)|Q(orig_group=group))
            else:
                raise PermissionDenied
        else: # get request user transfers
            sesar_user = request.user.sesaruser
            transfers = TransferHistory.objects.filter(Q(new_user=sesar_user)|Q(orig_user=sesar_user))

        if transfers:
            serializer = TransferSerializer(transfers, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'No transfers found'}, status=status.HTTP_404_NOT_FOUND)
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def create_transfer(request): 
    new_group = request.data.get('new_group') # new group name
    new_user = request.data.get('new_user') # new owner orcid
    orig_group = request.data.get('orig_group') # current group name
    orig_user = request.data.get('orig_user') # current owner orcid
    transfer_type = request.data.get('transfer_type') # values: all, user_code, sample_list
    user_code = request.data.get('user_code') # user code string
    sample_list = request.data.get('sample_list') # list of sample igsns
    sesar_user = request.user.sesaruser

    try:
        # is group transfer
        if orig_group:
            group = Group.objects.get(name=orig_group, part_of_group__isnull=True)
            if CanTransferGroupSample().has_object_permission(request, None, group):
                filters = {
                    'group_owner': group,
                }
            else:
                raise PermissionDenied
        else: # is user transfer
            if orig_user == sesar_user.orcid:
                filters = {
                    'cur_owner': sesar_user
                }
            else:
                raise PermissionDenied

        if transfer_type == 'user_code':
            if user_code:
                filters['igsn_prefix'] = user_code
            else:
                return Response({'error': 'Missing user code'}, status=status.HTTP_400_BAD_REQUEST)
        elif transfer_type == 'sample_list':
            if sample_list:
                filters['igsn__in'] = json.loads(sample_list)
            else:
                return Response({'error': 'Missing sample list'}, status=status.HTTP_400_BAD_REQUEST)
        
        samples = get_samples(filters, limit=None)

        if samples:
            serializer_data = {
                'transfer_by': sesar_user.pk,
                'orig_user': orig_user,
                'orig_group': orig_group,
                'new_user': new_user,
                'new_group': new_group,
                'status': 'pending',
                'data': {
                    'igsns': list(samples.values_list('igsn', flat=True))
                }
            }
            transfer = TransferWriteSerializer(data=serializer_data)
            if transfer.is_valid():
                new_transfer = transfer.save()
                samples.update(cur_owner=int(os.environ.get('SESAR_OWNER')), group_owner=None)
                return Response(TransferSerializer(new_transfer).data, status=status.HTTP_201_CREATED)
            else:
                return Response(transfer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'No samples found'}, status=status.HTTP_404_NOT_FOUND)
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


# update transfer, either accept/reject (by recipient), or cancel (by initiator)
@api_view(['POST'])
def update_transfer(request):
    try:
        id = request.data.get('id')
        transfer = TransferHistory.objects.get(pk=id, status='pending')
        samples = Sample.objects.filter(igsn__in=transfer.data['igsns'])
        sesar_user = request.user.sesaruser

        transfer_status = request.data.get('status')
        if transfer_status == 'completed' or transfer_status == 'rejected':
            # check user is recipient
            if transfer.new_user and transfer.new_user == sesar_user:
                if transfer_status == 'completed':
                    samples.update(req_registrant=None, cur_owner=transfer.new_user, group_owner=None)
                else: # rejected
                    samples.update(req_registrant=None, cur_owner=transfer.orig_user, group_owner=transfer.orig_group)
            # check user has permissions to manage transfer for group
            elif transfer.new_group and CanTransferGroupSample().has_object_permission(request, None, transfer.new_group):
                if transfer_status == 'completed':
                    samples.update(req_registrant=None, cur_owner=None, group_owner=transfer.new_group)
                else: # rejected
                    samples.update(req_registrant=None, cur_owner=transfer.orig_user, group_owner=transfer.orig_group)
            else:
                raise PermissionDenied
        elif transfer_status == 'canceled':
            # check user is initiator
            if transfer.orig_user and transfer.orig_user == sesar_user:
                samples.update(req_registrant=None, cur_owner=transfer.orig_user, group_owner=transfer.orig_group)
            # check user has permissions to manage transfer for group
            elif transfer.orig_group and CanTransferGroupSample().has_object_permission(request, None, transfer.orig_group):
                samples.update(req_registrant=None, cur_owner=transfer.orig_user, group_owner=transfer.orig_group)
            else:
                raise PermissionDenied

        transfer.status = transfer_status
        transfer.save()
        return Response({'Transfer updated with status {transfer.status}'}, status=status.HTTP_200_OK)

    except ObjectDoesNotExist:
        return Response({'error': 'Transfer not found'}, status=status.HTTP_404_NOT_FOUND)