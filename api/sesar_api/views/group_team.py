from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from datetime import *

from sesar_api.models import Group, GroupMember, SesarUser, Permission
from sesar_api.serializers import TeamSerializer, TeamWriteSerializer, SesarUserSerializer, PermissionSerializer
from sesar_api.permissions import CanAddGroupMember, CanDeleteGroupMember, CanAddGroup, CanChangeGroup, CanDeleteGroup
from sesar_api.views.group import normalize_name


# view all group teams
@api_view(['GET'])
def view_group_teams(request, name):
    try:
        group = request.user.sesaruser.groups.get(name=name, part_of_group__isnull=True)
        teams = Group.objects.filter(part_of_group=group)

        if teams:
            serializer = TeamSerializer(teams, many=True)
            return Response(serializer.data)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


# view group team
@api_view(['GET'])
def view_group_team(request, group, team):
    try:
        group = request.user.sesaruser.groups.get(name=group, part_of_group__isnull=True)
        team = Group.objects.get(part_of_group=group, name=team)

        if team:
            serializer = TeamSerializer(team)
            try:
                member_permissions = GroupMember.objects.get(sesar_user=request.user.sesaruser, group=group).auth_group.permissions
                member_permissions = list(member_permissions.values_list('codename', flat=True))
            except AttributeError:
                member_permissions = None
            try:
                team_permissions = Permission.objects.filter(group=team, auth_group__isnull=False)
                if team_permissions:
                    team_permissions = PermissionSerializer(team_permissions, many=True).data
                else:
                    team_permissions = None
            except:
                team_permissions = None
            return Response({
                'team': serializer.data,
                'member_permissions': member_permissions,
                'team_permissions': team_permissions
            }, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


# create group team, admin only
@api_view(['POST'])
def create_group_team(request):
    data = request.data.copy()
    data['name'] = data['name'].strip()
    data['display_name'] = data['name']
    data['name'] = normalize_name(data['name'])
    try:
        group = Group.objects.get(pk=data['part_of_group'])
        if CanAddGroup().has_object_permission(request, None, group):
            team = TeamWriteSerializer(data=data)
            if team.is_valid():
                team.save()
                return Response(team.data, status=status.HTTP_201_CREATED)
            else:
                return Response(team.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            raise PermissionDenied
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


# update group team information, admin only
@api_view(['POST'])
def update_group_team(request):
    try:
        team = Group.objects.get(pk=request.data['id'])
        if CanChangeGroup().has_object_permission(request, None, team.part_of_group):
            serializer = TeamWriteSerializer(team, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            raise PermissionDenied
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


# delete group team, admin only
@api_view(['POST'])
def delete_group_team(request):
    try:
        team = Group.objects.get(pk=request.data['id'])
        if CanDeleteGroup().has_object_permission(request, None, team.part_of_group):
            team.delete()
            return Response({'message': 'team deleted'}, status=status.HTTP_200_OK)
        else:
            raise PermissionDenied
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


# add group team member, admin only
@api_view(['POST'])
def add_group_team_member(request):
    try:
        team = Group.objects.get(pk=request.data['team'])
        sesar_user = SesarUser.objects.get(pk=request.data['member'])
        if CanAddGroupMember().has_object_permission(request, None, team.part_of_group):
            team.members.add(sesar_user)
            return Response(SesarUserSerializer(sesar_user).data, status=status.HTTP_201_CREATED)
        else:
            raise PermissionDenied
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


# remove group team member, admin only
@api_view(['POST'])
def remove_group_team_member(request):
    try:
        team = Group.objects.get(pk=request.data['team'])
        member = team.members.get(pk=request.data['member'])
        if CanDeleteGroupMember().has_object_permission(request, None, team.part_of_group):
            team.members.remove(member)
            return Response({'message': 'Team member removed.'}, status=status.HTTP_200_OK)
        else:
            raise PermissionDenied
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)