from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from datetime import *

from sesar_api.models import Team, TeamMember, SesarUser
from sesar_api.serializers import MemberSerializer, MemberWriteSerializer
from sesar_api.permissions import CanAddTeamMember, CanChangeTeamMember, CanDeleteTeamMember
from sesar_api.util import sesar_email


# view all team members
@api_view(['GET'])
def view_team_members(request, name):
    try:
        part_of_team = request.GET.get('part_of_team', None)
        if part_of_team:
            team = request.user.sesaruser.teams.get(name=part_of_team, part_of_team__isnull=True).teams.get(name=name)
        else:
            team = request.user.sesaruser.teams.get(name=name, part_of_team__isnull=True)
        members = TeamMember.objects.filter(team=team)

        if members:
            serializer = MemberSerializer(members, many=True)
            return Response(serializer.data)
        else:
            return Response({'message': 'No members found'}, status=status.HTTP_404_NOT_FOUND)
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


# create team member, admin only
@api_view(['POST'])
def create_team_member(request):
    try:
        team = Team.objects.get(pk=request.data['team'])
        if CanAddTeamMember().has_object_permission(request, None, team):
            member = MemberWriteSerializer(data=request.data)
            if member.is_valid():
                domain = request.get_host().replace("api", "app")
                link = domain + '/t/' + team.name
                recipient = SesarUser.objects.get(sesar_user_id=request.data['sesar_user'])
                sesar_email(
                    [recipient], 
                    f"You've been invited to the {team.display_name} team!",
                    f"Invited by {request.user.sesaruser.fname} {request.user.sesaruser.lname}",
                    None,
                    button={
                        'href': link,
                        'text': f'Join {team.display_name}'
                    }
                )
                new_member = member.save()
                return Response(MemberSerializer(new_member).data, status=status.HTTP_201_CREATED)
            else:
                return Response(member.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            raise PermissionDenied
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


# update team information, admin only
@api_view(['POST'])
def update_team_member(request):
    try:
        member = TeamMember.objects.get(pk=request.data['id'])
        if CanChangeTeamMember().has_object_permission(request, None, member.team):
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


# delete team member, admin only
@api_view(['POST'])
def delete_team_member(request):
    try:
        member = TeamMember.objects.get(pk=request.data['id'])
        if CanDeleteTeamMember(member).has_object_permission(request, None, member.team):
            member.delete()
            return Response({'message': 'team member deleted'}, status=status.HTTP_200_OK)
        else:
            raise PermissionDenied
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def accept_invitation(request):
    try:
        team = Team.objects.get(name=request.data['team_name'])
        member = TeamMember.objects.get(team=team, sesar_user=request.user.sesaruser, status='pending')
        if member:
            member.status = None
            member.save()
            return Response({'message': 'invitation accepted'}, status=status.HTTP_200_OK)
    except ObjectDoesNotExist:
        return Response({'error': 'no pending invitation found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def decline_invitation(request):
    try:
        team = Team.objects.get(name=request.data['team_name'])
        member = TeamMember.objects.get(team=team, sesar_user=request.user.sesaruser, status='pending')
        if member:
            member.delete()
            return Response({'message': 'invitation declined'}, status=status.HTTP_200_OK)
    except ObjectDoesNotExist:
        return Response({'error': 'no pending invitation found'}, status=status.HTTP_404_NOT_FOUND)