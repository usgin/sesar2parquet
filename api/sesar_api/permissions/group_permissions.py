from rest_framework import permissions
from sesar_api.models import GroupMember


class IsGroupOwner(permissions.BasePermission):
    message = 'Permission denied. This group is not owned by you.'

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user.sesaruser


class IsGroupAdmin(permissions.BasePermission):
    message = 'Permission denied. You are not an admin of this group.'

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj):
        if GroupMember.objects.filter(
            group=obj,
            sesar_user=request.user.sesaruser, 
            is_admin=True).exists():
            return True
        else:
            return False
