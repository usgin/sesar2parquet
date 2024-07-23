from rest_framework import permissions
from sesar_api.models import OrganizationMember


class IsOrganizationOwner(permissions.BasePermission):
    message = 'Permission denied. This organization is not owned by you.'

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user.sesaruser


class IsOrganizationAdmin(permissions.BasePermission):
    message = 'Permission denied. You are not an admin of this organization.'

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj):
        if OrganizationMember.objects.filter(
            organization=obj,
            sesar_user=request.user.sesaruser, 
            is_admin=True).exists():
            return True
        else:
            return False
