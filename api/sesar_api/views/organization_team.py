from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from datetime import *

from sesar_api.models import Organization, OrganizationTeam, OrganizationMember
from sesar_api.serializers import TeamSerializer, TeamWriteSerializer
from sesar_api.permissions import IsOrganizationAdmin


# view all organization teams
@api_view(['GET'])
def view_organization_teams(request, name):
    try:
        organization = request.user.sesaruser.organizations.get(name=name)
        teams = OrganizationTeam.objects.filter(organization=organization)

        if teams:
            serializer = TeamSerializer(teams, many=True)
            return Response(serializer.data)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


# view all organization teams
@api_view(['GET'])
def view_organization_team(request, organization, team):
    try:
        organization = request.user.sesaruser.organizations.get(name=organization)
        team = OrganizationTeam.objects.get(organization=organization, name=team)

        if team:
            serializer = TeamSerializer(team)
            return Response(serializer.data)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


# create organization team, admin only
@api_view(['POST'])
def create_organization_team(request):
    try:
        organization = Organization.objects.get(pk=request.data['organization'])
        if IsOrganizationAdmin().has_object_permission(request, None, organization):
            team = TeamWriteSerializer(data=request.data)
            if team.is_valid():
                team.save()
                return Response(team.data, status=status.HTTP_201_CREATED)
            else:
                return Response(team.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            raise PermissionDenied
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


# update organization team information, admin only
@api_view(['POST'])
def update_organization_team(request):
    try:
        team = OrganizationTeam.objects.get(pk=request.data['id'])
        if IsOrganizationAdmin().has_object_permission(request, None, team.organization):
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


# delete organization team, admin only
@api_view(['POST'])
def delete_organization_team(request):
    try:
        team = OrganizationTeam.objects.get(pk=request.data['id'])
        if IsOrganizationAdmin().has_object_permission(request, None, team.organization):
            team.delete()
            return Response(status=status.HTTP_200_OK)
        else:
            raise PermissionDenied
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


# add organization team member, admin only
@api_view(['POST'])
def add_organization_team_member(request):
    try:
        team = OrganizationTeam.objects.get(pk=request.data['team'])
        member = OrganizationMember.objects.get(pk=request.data['member'])
        if IsOrganizationAdmin().has_object_permission(request, None, team.organization):
            team.members.add(member)
            return Response(status=status.HTTP_200_OK)
        else:
            raise PermissionDenied
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


# remove organization team member, admin only
@api_view(['POST'])
def remove_organization_team_member(request):
    try:
        team = OrganizationTeam.objects.get(pk=request.data['team'])
        member = team.members.get(pk=request.data['member'])
        if IsOrganizationAdmin().has_object_permission(request, None, team.organization):
            team.members.remove(member)
            return Response(status=status.HTTP_200_OK)
        else:
            raise PermissionDenied
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)