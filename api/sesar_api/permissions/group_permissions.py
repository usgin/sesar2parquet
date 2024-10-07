from rest_framework import permissions
from sesar_api.models import GroupMember


class IsGroupOwner(permissions.BasePermission):
    message = 'Permission denied. This group is not owned by you.'

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user.sesaruser


class CanAddGroupMember(permissions.BasePermission):
    message = 'Permission denied. Cannot add group member.'

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj):
        try:
            if GroupMember.objects.get(group=obj, sesar_user=request.user.sesaruser).auth_group.permissions.filter(codename='add_groupmember').exists():
                return True
        except (GroupMember.DoesNotExist, AttributeError):
            return False

        return False

class CanChangeGroupMember(permissions.BasePermission):
    message = 'Permission denied. Cannot change group member.'

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj):
        try:
            if GroupMember.objects.get(group=obj, sesar_user=request.user.sesaruser).auth_group.permissions.filter(codename='change_groupmember').exists():
                return True
        except (GroupMember.DoesNotExist, AttributeError):
            return False

        return False

class CanDeleteGroupMember(permissions.BasePermission):
    message = 'Permission denied. Cannot delete group member.'

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj):
        try:
            if GroupMember.objects.get(group=obj, sesar_user=request.user.sesaruser).auth_group.permissions.filter(codename='delete_groupmember').exists():
                return True
        except (GroupMember.DoesNotExist, AttributeError):
            return False

        return False

class CanAddGroup(permissions.BasePermission):
    message = 'Permission denied. Cannot add group.'

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj):
        try:
            if GroupMember.objects.get(group=obj, sesar_user=request.user.sesaruser).auth_group.permissions.filter(codename='add_group').exists():
                return True
        except (GroupMember.DoesNotExist, AttributeError):
            return False

        return False

class CanChangeGroup(permissions.BasePermission):
    message = 'Permission denied. Cannot change group.'

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj):
        try:
            if GroupMember.objects.get(group=obj, sesar_user=request.user.sesaruser).auth_group.permissions.filter(codename='change_group').exists():
                return True
        except (GroupMember.DoesNotExist, AttributeError):
            return False

        return False

class CanDeleteGroup(permissions.BasePermission):
    message = 'Permission denied. Cannot delete group.'

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj):
        try:
            if GroupMember.objects.get(group=obj, sesar_user=request.user.sesaruser).auth_group.permissions.filter(codename='delete_group').exists():
                return True
        except (GroupMember.DoesNotExist, AttributeError):
            return False

        return False