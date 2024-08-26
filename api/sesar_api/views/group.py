from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from datetime import *

from sesar_api.models import Group
from sesar_api.serializers import GroupSerializer, GroupWriteSerializer, MemberWriteSerializer
from sesar_api.permissions import IsGroupAdmin, IsGroupOwner

# view an group, request user must be a member
@api_view(['GET'])
def view_group(request, name):
    try:
        group = request.user.sesaruser.groups.get(name=name)
    
        if group:
            serializer = GroupSerializer(group)
            return Response(serializer.data)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


# get all groups of request user
@api_view(['GET'])
def view_user_groups(request):
    groups = request.user.sesaruser.groups
 
    if groups:
        serializer = GroupSerializer(groups, many=True)
        return Response(serializer.data)
    else:
        return Response(status=status.HTTP_404_NOT_FOUND)


# create group
@api_view(['POST'])
def create_group(request):
    data = request.data.copy()
    data['owner'] = request.user.sesaruser.pk
    group = GroupWriteSerializer(data=data)
    if group.is_valid():
        created_org = group.save()
        # add owner as a member with admin role
        owner = MemberWriteSerializer(data={
            'group':created_org.pk,
            'sesar_user':request.user.sesaruser.pk,
            'is_admin': True
        })
        if owner.is_valid():
            owner.save()
        else:
            return Response(owner.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(group.data, status=status.HTTP_201_CREATED)
    else:
        return Response(group.errors, status=status.HTTP_400_BAD_REQUEST)


# update group information, admin only
@api_view(['POST'])
def update_group(request):
    try:
        group = Group.objects.get(pk=request.data['id'], deactivate_date=None)
        if IsGroupAdmin().has_object_permission(request, None, group):
            serializer = GroupWriteSerializer(group, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            raise PermissionDenied
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


# deactivate group, owner only
@api_view(['POST'])
def deactivate_group(request):
    try:
        group = Group.objects.get(pk=request.data['id'], deactivate_date=None)

        if group.owned_samples_set.exists():
            return Response({"detail": "You cannot deactivate an group that owns samples. Please transfer the ownership of any group owned samples first."}, status=status.HTTP_400_BAD_REQUEST)
        if IsGroupOwner().has_object_permission(request, None, group):
            serializer = GroupWriteSerializer(group, data={'deactivate_date':datetime.now()}, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            raise PermissionDenied
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


# transfer group ownership, owner only
@api_view(['POST'])
def transfer_group(request):
    try:
        group = Group.objects.get(pk=request.data['id'], deactivate_date=None)
        if IsGroupOwner().has_object_permission(request, None, group):
            serializer = GroupWriteSerializer(group, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            raise PermissionDenied
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)