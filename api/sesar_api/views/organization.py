from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from datetime import *

from requests.exceptions import HTTPError
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied

from sesar_api.permissions import CanCreateSample, IsUserCodeOwner, IsOrganizationAdmin, IsOrganizationOwner
from sesar_api.models import SesarUserCode, Organization, SesarUser, Sample
from sesar_api.serializers import OrganizationSerializer, OrganizationWriteSerializer, MemberSerializer, MemberWriteSerializer


# view an organization, request user must be a member
@api_view(['GET'])
def view_organization(request, pk):
    organization = request.user.sesaruser.organizations.get(pk=pk)
 
    if organization:
        serializer = OrganizationSerializer(organization)
        return Response(serializer.data)
    else:
        return Response(status=status.HTTP_404_NOT_FOUND)


# get all organizations of request user
@api_view(['GET'])
def view_user_organizations(request):
    organizations = request.user.sesaruser.organizations
 
    if organizations:
        serializer = OrganizationSerializer(organizations, many=True)
        return Response(serializer.data)
    else:
        return Response(status=status.HTTP_404_NOT_FOUND)


# create organization
@api_view(['POST'])
def create_organization(request):
    request.data['owner'] = request.user.sesaruser.pk
    organization = OrganizationWriteSerializer(data=request.data)
    if organization.is_valid():
        created_org = organization.save()
        # add owner as a member with admin role
        owner = MemberWriteSerializer(data={
            'organization':created_org.pk,
            'sesar_user':request.user.sesaruser.pk,
            'is_admin': True
        })
        if owner.is_valid():
            owner.save()
        else:
            return Response(owner.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(organization.data, status=status.HTTP_201_CREATED)
    else:
        return Response(organization.errors, status=status.HTTP_400_BAD_REQUEST)


# update organization information, admin only
@api_view(['POST'])
def update_organization(request, pk):
    try:
        organization = Organization.objects.get(pk=pk, deactivate_date=None)
        if IsOrganizationAdmin().has_object_permission(request, None, organization):
            serializer = OrganizationSerializer(organization, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            raise PermissionDenied
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


# deactivate organization, owner only
@api_view(['POST'])
@permission_classes([IsOrganizationOwner])
def deactivate_organization(request, pk):
    try:
        organization = Organization.objects.get(pk=pk, deactivate_date=None)

        if organization.owned_samples_set:
            return Response({"detail": "You cannot deactivate an organization that owns samples. Please transfer the ownership of any organization owned samples first."}, status=status.HTTP_400_BAD_REQUEST)
        if IsOrganizationOwner().has_object_permission(request, None, organization):
            serializer = OrganizationWriteSerializer(organization, data={'deactivate_date':datetime.now()}, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            raise PermissionDenied
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


# transfer organization ownership, owner only
@api_view(['POST'])
@permission_classes([IsOrganizationOwner])
def transfer_organization(request, pk):
    try:
        organization = Organization.objects.get(pk=pk, deactivate_date=None)
        if IsOrganizationOwner().has_object_permission(request, None, organization):
            serializer = OrganizationWriteSerializer(organization, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            raise PermissionDenied
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)