from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from datetime import *
from django.db.models import Q
import re

from sesar_api.models import Team, TeamMember
from sesar_api.serializers import TeamSerializer, TeamWriteSerializer, MemberWriteSerializer
from sesar_api.permissions import IsTeamOwner, CanChangeTeam
from django.contrib.auth.models import Group as AuthGroup


def normalize_name(name):
    return re.sub(r'[^a-zA-Z0-9-]', '-', name.strip().lower())


# view a team, request user must be a member
@api_view(['GET'])
def view_team(request, name):
    try:
        team = request.user.sesaruser.teams.prefetch_related('members').get(name=name, part_of_team__isnull=True, deactivate_date__isnull=True)
        if team:
            team_member = TeamMember.objects.get(sesar_user=request.user.sesaruser, team=team)
            if team_member.status == 'pending':
                return Response({
                    'membership_status': 'pending'
                }, status=status.HTTP_200_OK)
            serializer = TeamSerializer(team)
            try:
                permissions = team_member.auth_group.permissions
                permissions = list(permissions.values_list('codename', flat=True))
            except AttributeError:
                permissions = []
            return Response({
                'team': serializer.data,
                'permissions': permissions
            }, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


# get all teams of request user
@api_view(['GET'])
def view_user_teams(request):
    teams = request.user.sesaruser.teams.filter(part_of_team__isnull=True, deactivate_date__isnull=True)
 
    if teams:
        serializer = TeamSerializer(teams, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(status=status.HTTP_404_NOT_FOUND)


# create team
@api_view(['POST'])
def create_team(request):
    data = request.data.copy()
    data['owner'] = request.user.sesaruser.orcid
    data['name'] = data['name'].strip()
    data['display_name'] = data['name']
    data['name'] = normalize_name(data['name'])
    team = TeamWriteSerializer(data=data)
    if team.is_valid():
        created_org = team.save()
        # add owner as a member with owner role
        owner = MemberWriteSerializer(data={
            'team':created_org.pk,
            'sesar_user':request.user.sesaruser.pk,
            'auth_group':'Team Owner'
        })
        if owner.is_valid():
            owner.save()
        else:
            return Response(owner.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(team.data, status=status.HTTP_201_CREATED)
    else:
        return Response(team.errors, status=status.HTTP_400_BAD_REQUEST)


# update team information, admin only
@api_view(['POST'])
def update_team(request):
    try:
        if 'part_of_team' in request.data:
            part_of_team = Team.objects.get(name=request.data['part_of_team'], part_of_team__isnull=True)
        else:
            part_of_team = None
        team = Team.objects.get(name=request.data['team_name'], deactivate_date=None, part_of_team=part_of_team)
        if CanChangeTeam().has_object_permission(request, None, team):
            serializer = TeamWriteSerializer(team, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            raise PermissionDenied
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


# deactivate team, owner only
@api_view(['POST'])
def deactivate_team(request):
    try:
        team = Team.objects.get(name=request.data['name'], deactivate_date=None)

        if team.owned_samples_set.exists():
            return Response({"error": "You cannot deactivate a team that owns samples. Please transfer the ownership of any team owned samples first."}, status=status.HTTP_400_BAD_REQUEST)
        if IsTeamOwner().has_object_permission(request, None, team):
            serializer = TeamWriteSerializer(team, data={'deactivate_date':datetime.now()}, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            raise PermissionDenied
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


# transfer team ownership, owner only
@api_view(['POST'])
def transfer_team(request):
    try:
        team = Team.objects.get(name=request.data['name'], deactivate_date=None)
        if IsTeamOwner().has_object_permission(request, None, team):
            serializer = TeamWriteSerializer(team, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            raise PermissionDenied
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


# search for team by name
@api_view(['GET'])
def search_teams(request):
    query = request.GET.get('query', '')
    limit = int(request.GET.get('limit', 10))
    try:
        # search for user using name or orcid
        teams = Team.objects.filter(
            Q(part_of_team__isnull=True) &
            Q(name__icontains=query) |
            Q(display_name__icontains=query)
        )[:limit]

        if teams:
            serializer = TeamSerializer(teams, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)
    except:
        return Response(status=status.HTTP_404_NOT_FOUND)