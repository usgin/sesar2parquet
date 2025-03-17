from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from sesar_api.models import SesarCode, Team
from sesar_api.serializers import SesarCodeSerializer, SesarCodeWriteSerializer
from sesar_api.permissions import CanAddTeamSesarCode, CanDeleteTeamSesarCode


# view a Sesar code
@api_view(['GET'])
def view_sesar_code(request, sesar_code):
    try:
        sesar_code = SesarCode.objects.get(sesar_code=sesar_code)
        if sesar_code:
            serializer = SesarCodeSerializer(sesar_code)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)
    except SesarCode.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


# get all Sesar codes of request user
@api_view(['GET'])
def view_user_sesar_codes(request):
    sesar_codes = request.user.sesaruser.sesar_codes

    if sesar_codes:
        serializer = SesarCodeSerializer(sesar_codes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(status=status.HTTP_404_NOT_FOUND)


# get all Sesar codes of team
@api_view(['GET'])
def view_team_sesar_codes(request, name):
    try:
        team = Team.objects.get(name=name, part_of_team__isnull=True)
    
        if team and team.sesar_codes.count() > 0:
            serializer = SesarCodeSerializer(team.sesar_codes, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'No team owned Sesar codes found'}, status=status.HTTP_404_NOT_FOUND)
    except Team.DoesNotExist:
        Response({'error': 'Team does not exist'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def create_sesar_code(request):
    try:
        can_create = False
        
        # individuals can create Sesar codes they own
        if 'sesar_user' in request.data:
            can_create = True
        # need to check if user has permissions to create team owned code
        elif 'team' in request.data:
            team = request.user.sesaruser.teams.get(name=request.data['team'], part_of_team__isnull=True)
            if CanAddTeamSesarCode().has_object_permission(request, None, team):
                can_create = True

        if can_create:
            sesar_code = SesarCodeWriteSerializer(data=request.data)
            if sesar_code.is_valid():
                new_sesar_code = sesar_code.save()
                return Response(SesarCodeSerializer(new_sesar_code).data, status=status.HTTP_201_CREATED)
            else:
                return Response(sesar_code.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            raise PermissionDenied
    except IntegrityError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def delete_sesar_code(request):
    try:
        can_delete = False
        sesar_code = SesarCode.objects.get(sesar_code=request.data['sesar_code'])

        if sesar_code.samples.exists():
            return Response({"error": "You cannot delete a Sesar code with samples."}, status=status.HTTP_400_BAD_REQUEST)
        
        # if owned by individual
        if sesar_code.sesar_user:
            can_delete = False # TODO: add individual level permission for deletion
        # if owned by team
        if sesar_code.team:
            if CanDeleteTeamSesarCode().has_object_permission(request, None, sesar_code.team):
                can_delete = True

        if can_delete:
            sesar_code.delete()
            return Response({'message': 'Sesar code deleted'}, status=status.HTTP_200_OK)
        else:
            raise PermissionDenied
    except SesarCode.DoesNotExist:
        return Response({'error': 'Sesar code does not exist'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': e}, status=status.HTTP_400_BAD_REQUEST)