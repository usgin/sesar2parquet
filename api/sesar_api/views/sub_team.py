from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from datetime import *

from sesar_api.models import Team, TeamMember, SesarUser, Permission
from sesar_api.serializers import SubTeamSerializer, SubTeamWriteSerializer, SesarUserSerializer, PermissionSerializer
from sesar_api.permissions import CanAddTeamMember, CanDeleteTeamMember, CanAddTeam, CanChangeTeam, CanDeleteTeam
from sesar_api.views.team import normalize_name


# view all subteams
@api_view(['GET'])
def view_subteams(request, name):
    try:
        team = request.user.sesaruser.teams.get(name=name, part_of_team__isnull=True)
        subteams = Team.objects.filter(part_of_team=team)

        if subteams:
            serializer = SubTeamSerializer(subteams, many=True)
            return Response(serializer.data)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


# view subteam
@api_view(['GET'])
def view_subteam(request, team, subteam):
    try:
        team = request.user.sesaruser.teams.get(name=team, part_of_team__isnull=True)
        subteam = Team.objects.get(part_of_team=team, name=subteam)

        if subteam:
            serializer = SubTeamSerializer(subteam)
            try:
                member_permissions = TeamMember.objects.get(sesar_user=request.user.sesaruser, team=team).auth_group.permissions
                member_permissions = list(member_permissions.values_list('codename', flat=True))
            except AttributeError:
                member_permissions = None
            try:
                subteam_permissions = Permission.objects.filter(team=subteam, auth_group__isnull=False)
                if subteam_permissions:
                    subteam_permissions = PermissionSerializer(subteam_permissions, many=True).data
                else:
                    subteam_permissions = None
            except:
                subteam_permissions = None
            return Response({
                'subteam': serializer.data,
                'member_permissions': member_permissions,
                'subteam_permissions': subteam_permissions
            }, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


# create subteam, admin only
@api_view(['POST'])
def create_subteam(request):
    data = request.data.copy()
    data['name'] = data['name'].strip()
    data['display_name'] = data['name']
    data['name'] = normalize_name(data['name'])
    try:
        team = Team.objects.get(pk=data['part_of_team'])
        if CanAddTeam().has_object_permission(request, None, team):
            subteam = SubTeamWriteSerializer(data=data)
            if subteam.is_valid():
                subteam.save()
                return Response(subteam.data, status=status.HTTP_201_CREATED)
            else:
                return Response(subteam.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            raise PermissionDenied
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


# update subteam information, admin only
@api_view(['POST'])
def update_subteam(request):
    try:
        subteam = Team.objects.get(pk=request.data['id'])
        if CanChangeTeam().has_object_permission(request, None, subteam.part_of_team):
            serializer = SubTeamWriteSerializer(subteam, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            raise PermissionDenied
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


# delete subteam, admin only
@api_view(['POST'])
def delete_subteam(request):
    try:
        subteam = Team.objects.get(pk=request.data['id'])
        if CanDeleteTeam().has_object_permission(request, None, subteam.part_of_team):
            subteam.delete()
            return Response({'message': 'subteam deleted'}, status=status.HTTP_200_OK)
        else:
            raise PermissionDenied
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


# add subteam member, admin only
@api_view(['POST'])
def add_subteam_member(request):
    try:
        subteam = Team.objects.get(pk=request.data['subteam'])
        sesar_user = SesarUser.objects.get(pk=request.data['member'])
        if CanAddTeamMember().has_object_permission(request, None, subteam.part_of_team):
            subteam.members.add(sesar_user)
            return Response(SesarUserSerializer(sesar_user).data, status=status.HTTP_201_CREATED)
        else:
            raise PermissionDenied
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


# remove subteam member, admin only
@api_view(['POST'])
def remove_subteam_member(request):
    try:
        team = Team.objects.get(pk=request.data['subteam'])
        member = team.members.get(pk=request.data['member'])
        if CanDeleteTeamMember().has_object_permission(request, None, team.part_of_team):
            team.members.remove(member)
            return Response({'message': 'Team member removed.'}, status=status.HTTP_200_OK)
        else:
            raise PermissionDenied
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)