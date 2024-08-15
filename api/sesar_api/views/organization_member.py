from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from datetime import *

from sesar_api.models import Organization, OrganizationMember
from sesar_api.serializers import MemberSerializer, MemberWriteSerializer
from sesar_api.permissions import IsOrganizationAdmin


# view all organization members
@api_view(['GET'])
def view_organization_members(request, name):
    try:
        organization = request.user.sesaruser.organizations.get(name=name)
        members = OrganizationMember.objects.filter(organization=organization)

        if members:
            serializer = MemberSerializer(members, many=True)
            return Response(serializer.data)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


# create organization member, admin only
@api_view(['POST'])
def create_organization_member(request):
    try:
        organization = Organization.objects.get(pk=request.data['organization'])
        if IsOrganizationAdmin().has_object_permission(request, None, organization):
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


# update organization information, admin only
@api_view(['POST'])
def update_organization_member(request):
    try:
        member = OrganizationMember.objects.get(pk=request.data['id'])
        if IsOrganizationAdmin().has_object_permission(request, None, member.organization):
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


# delete organization member, admin only
@api_view(['POST'])
def delete_organization_member(request):
    try:
        member = OrganizationMember.objects.get(pk=request.data['id'])
        if IsOrganizationAdmin().has_object_permission(request, None, member.organization):
            member.delete()
            return Response(status=status.HTTP_200_OK)
        else:
            raise PermissionDenied
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)