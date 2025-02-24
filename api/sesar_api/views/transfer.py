from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db.models import Q
import os
import json

from sesar_api.serializers import TransferSerializer, TransferWriteSerializer
from sesar_api.permissions import CanTransferTeamSample
from sesar_api.models import TransferHistory, Sample, Team

from sesar_api.util import get_samples


# get all transfers
@api_view(['GET'])
def view_transfers(request):
    try:
        # get team transfers
        if request.GET.get('team', False):
            team = Team.objects.get(name=request.GET.get('team'), part_of_team__isnull=True)
            if CanTransferTeamSample().has_object_permission(request, None, team):
                transfers = TransferHistory.objects.filter(Q(new_team=team)|Q(orig_team=team))
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
    new_team = request.data.get('new_team') # new team name
    new_user = request.data.get('new_user') # new owner orcid
    orig_team = request.data.get('orig_team') # current team name
    orig_user = request.data.get('orig_user') # current owner orcid
    transfer_type = request.data.get('transfer_type') # values: all, user_code, sample_list
    user_code = request.data.get('user_code') # user code string
    sample_list = request.data.get('sample_list') # list of sample igsns
    sesar_user = request.user.sesaruser

    try:
        # is team transfer
        if orig_team:
            team = Team.objects.get(name=orig_team, part_of_team__isnull=True)
            if CanTransferTeamSample().has_object_permission(request, None, team):
                filters = {
                    'team_owner': team,
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
        
        samples = get_samples(filters)

        if samples:
            serializer_data = {
                'transfer_by': sesar_user.pk,
                'orig_user': orig_user,
                'orig_team': orig_team,
                'new_user': new_user,
                'new_team': new_team,
                'status': 'pending',
                'data': {
                    'igsns': list(samples.values_list('igsn', flat=True))
                }
            }
            transfer = TransferWriteSerializer(data=serializer_data)
            if transfer.is_valid():
                new_transfer = transfer.save()
                samples.update(cur_owner=int(os.environ.get('SESAR_OWNER')), team_owner=None)
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
                    samples.update(req_registrant=None, cur_owner=transfer.new_user, team_owner=None)
                else: # rejected
                    samples.update(req_registrant=None, cur_owner=transfer.orig_user, team_owner=transfer.orig_team)
            # check user has permissions to manage transfer for team
            elif transfer.new_team and CanTransferTeamSample().has_object_permission(request, None, transfer.new_team):
                if transfer_status == 'completed':
                    samples.update(req_registrant=None, cur_owner=None, team_owner=transfer.new_team)
                else: # rejected
                    samples.update(req_registrant=None, cur_owner=transfer.orig_user, team_owner=transfer.orig_team)
            else:
                raise PermissionDenied
        elif transfer_status == 'canceled':
            # check user is initiator
            if transfer.orig_user and transfer.orig_user == sesar_user:
                samples.update(req_registrant=None, cur_owner=transfer.orig_user, team_owner=transfer.orig_team)
            # check user has permissions to manage transfer for team
            elif transfer.orig_team and CanTransferTeamSample().has_object_permission(request, None, transfer.orig_team):
                samples.update(req_registrant=None, cur_owner=transfer.orig_user, team_owner=transfer.orig_team)
            else:
                raise PermissionDenied

        transfer.status = transfer_status
        transfer.save()
        return Response({'Transfer updated with status {transfer.status}'}, status=status.HTTP_200_OK)

    except ObjectDoesNotExist:
        return Response({'error': 'Transfer not found'}, status=status.HTTP_404_NOT_FOUND)