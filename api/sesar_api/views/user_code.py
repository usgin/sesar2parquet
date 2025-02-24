from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from sesar_api.models import SesarUserCode, Team
from sesar_api.serializers import UserCodeSerializer, UserCodeWriteSerializer
from sesar_api.permissions import CanAddTeamUserCode, CanDeleteTeamUserCode


# view a user code
@api_view(['GET'])
def view_user_code(request, user_code):
    try:
        user_code = SesarUserCode.objects.get(user_code=user_code)
        if user_code:
            serializer = UserCodeSerializer(user_code)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)
    except SesarUserCode.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


# get all user codes of request user
@api_view(['GET'])
def view_user_user_codes(request):
    user_codes = request.user.sesaruser.user_codes

    if user_codes:
        serializer = UserCodeSerializer(user_codes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(status=status.HTTP_404_NOT_FOUND)


# get all user codes of team
@api_view(['GET'])
def view_team_user_codes(request, name):
    try:
        team = Team.objects.get(name=name, part_of_team__isnull=True)
    
        if team and team.user_codes.count() > 0:
            serializer = UserCodeSerializer(team.user_codes, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'No team owned user codes found'}, status=status.HTTP_404_NOT_FOUND)
    except Team.DoesNotExist:
        Response({'error': 'Team does not exist'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def create_user_code(request):
    try:
        can_create = False
        
        # individuals can create user codes they own
        if 'sesar_user' in request.data:
            can_create = True
        # need to check if user has permissions to create team owned code
        elif 'team' in request.data:
            team = request.user.sesaruser.teams.get(name=request.data['team'], part_of_team__isnull=True)
            if CanAddTeamUserCode().has_object_permission(request, None, team):
                can_create = True

        if can_create:
            user_code = UserCodeWriteSerializer(data=request.data)
            if user_code.is_valid():
                new_user_code = user_code.save()
                return Response(UserCodeSerializer(new_user_code).data, status=status.HTTP_201_CREATED)
            else:
                return Response(user_code.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            raise PermissionDenied
    except IntegrityError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def delete_user_code(request):
    try:
        can_delete = False
        user_code = SesarUserCode.objects.get(user_code=request.data['user_code'])

        if user_code.samples.exists():
            return Response({"error": "You cannot delete a user code with samples."}, status=status.HTTP_400_BAD_REQUEST)
        
        # if owned by individual
        if user_code.sesar_user:
            can_delete = False # TODO: add individual level permission for deletion
        # if owned by team
        if user_code.team:
            if CanDeleteTeamUserCode().has_object_permission(request, None, user_code.team):
                can_delete = True

        if can_delete:
            user_code.delete()
            return Response({'message': 'user code deleted'}, status=status.HTTP_200_OK)
        else:
            raise PermissionDenied
    except SesarUserCode.DoesNotExist:
        return Response({'error': 'user code does not exist'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': e}, status=status.HTTP_400_BAD_REQUEST)