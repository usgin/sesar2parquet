from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db.models import Q

from sesar_api.models import Permission, Team, Sample, SesarUserCode
from sesar_api.serializers import PermissionSerializer, PermissionWriteSerializer
from sesar_api.permissions import CanGrantSamplePermission, CanGrantUserCodePermission, CanEditPermission


# get user permissions
@api_view(['GET'])
def view_user_permissions(request):
    permissions = Permission.objects.filter(sesar_user=request.user.sesaruser)

    serializer = PermissionSerializer(permissions, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


# get permissions user shared to others
@api_view(['GET'])
def view_user_permissions_shared_to_others(request):
    permissions = Permission.objects.filter(Q(sample__cur_owner=request.user.sesaruser) | Q(user_code__sesar_user=request.user.sesaruser))

    serializer = PermissionSerializer(permissions, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

# get team permissions
# get permissions shared to team and shared by team
# function should work with sub teams
@api_view(['GET'])
def view_team_permissions(request, name):
    try:
        part_of_team = request.GET.get('part_of_team', None)
        if part_of_team:
            part_of_team = Team.objects.get(name=part_of_team, part_of_team__isnull=True)
        team = Team.objects.get(name=name, part_of_team=part_of_team)
        if team:
            shared_to_team = Permission.objects.filter(team=team)

            shared_by_team = Permission.objects.filter(granted_by_team=team)

            to_serializer = PermissionSerializer(shared_to_team, many=True)
            by_serializer = PermissionSerializer(shared_by_team, many=True)
            return Response({'shared_to_team':to_serializer.data,'shared_by_team':by_serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'team not found'}, status=status.HTTP_404_NOT_FOUND)
    except ObjectDoesNotExist:
        return Response({'error': 'team not found'}, status=status.HTTP_404_NOT_FOUND)


# create permission, admin only
@api_view(['POST'])
def create_permission(request):
    granted_by_team = None
    sample = None
    user_code = None
    try:
        if 'granted_by_team' in request.data:
            granted_by_team = Team.objects.filter(pk=request.data['granted_by_team'], part_of_team__isnull=True).first()
        if 'sample' in request.data:
            sample = Sample.objects.filter(igsn=request.data['sample']).first()
        if 'user_code' in request.data:
            user_code = SesarUserCode.objects.filter(user_code=request.data['user_code']).first()

        auth_group = request.data['auth_group']

        if ((sample and CanGrantSamplePermission(granted_by_team, permissions_to_grant=auth_group).has_object_permission(request, None, sample)) or
            (user_code and CanGrantUserCodePermission(granted_by_team,permissions_to_grant=auth_group).has_object_permission(request, None, user_code))):
                permission = PermissionWriteSerializer(data=request.data)
                if permission.is_valid():
                    new_permission = permission.save()
                    return Response(PermissionSerializer(new_permission).data, status=status.HTTP_201_CREATED)
                else:
                    return Response(permission.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            raise PermissionDenied
    except ObjectDoesNotExist:
        return Response({'error': 'permission not found'}, status=status.HTTP_404_NOT_FOUND)


# update permission, admin only
@api_view(['POST'])
def update_permission(request):
    try:
        permission = Permission.objects.get(pk=request.data['id'])
        if CanEditPermission().has_object_permission(request, None, permission):
            serializer = PermissionWriteSerializer(permission, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            raise PermissionDenied
    except ObjectDoesNotExist:
        return Response({'error': 'permission not found'}, status=status.HTTP_404_NOT_FOUND)


# delete permission, admin only
@api_view(['POST'])
def delete_permission(request):
    try:
        permission = Permission.objects.get(pk=request.data['id'])
        if CanEditPermission().has_object_permission(request, None, permission):
            permission.delete()
            return Response({'message': 'Permission removed.'}, status=status.HTTP_200_OK)
        else:
            raise PermissionDenied
    except ObjectDoesNotExist:
        return Response({'error': 'permission not found'}, status=status.HTTP_404_NOT_FOUND)