from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from datetime import *

from sesar_api.models import Group, GroupMember
from sesar_api.serializers import MemberSerializer, MemberWriteSerializer
from sesar_api.permissions import CanAddGroupMember, CanChangeGroupMember, CanDeleteGroupMember


# view all group members
@api_view(['GET'])
def view_group_members(request, name):
    try:
        group = request.user.sesaruser.groups.get(name=name)
        members = GroupMember.objects.filter(group=group)

        if members:
            serializer = MemberSerializer(members, many=True)
            return Response(serializer.data)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


# create group member, admin only
@api_view(['POST'])
def create_group_member(request):
    try:
        group = Group.objects.get(pk=request.data['group'])
        if CanAddGroupMember().has_object_permission(request, None, group):
            member = MemberWriteSerializer(data=request.data)
            if member.is_valid():
                member.save()
                return Response(member.data, status=status.HTTP_201_CREATED)
            else:
                return Response(member.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            raise PermissionDenied
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


# update group information, admin only
@api_view(['POST'])
def update_group_member(request):
    try:
        member = GroupMember.objects.get(pk=request.data['id'])
        if CanChangeGroupMember().has_object_permission(request, None, member.group):
            serializer = MemberWriteSerializer(member, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            raise PermissionDenied
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


# delete group member, admin only
@api_view(['POST'])
def delete_group_member(request):
    try:
        member = GroupMember.objects.get(pk=request.data['id'])
        if CanDeleteGroupMember().has_object_permission(request, None, member.group):
            member.delete()
            return Response(status=status.HTTP_200_OK)
        else:
            raise PermissionDenied
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)