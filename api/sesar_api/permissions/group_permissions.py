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

    def __init__(self, member=None):
        # for the case where permissions were originally shared to a group, but the user code is not owned by the group
        # the permissions should only be shared within that group and within the bounds of the original granted permissions
        self.member = member

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj):
        try:
            if GroupMember.objects.get(group=obj, sesar_user=request.user.sesaruser).auth_group.permissions.filter(codename='delete_groupmember').exists():
                return True
            if request.user.sesaruser == self.member and obj.owner != self.member: # user can remove themselves
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


class CanViewGroupSamples(permissions.BasePermission):
    message = 'Permission denied. Cannot view group samples.'

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj):
        try:
            if GroupMember.objects.get(group=obj, sesar_user=request.user.sesaruser).auth_group.permissions.filter(codename='view_sample').exists():
                return True
        except (GroupMember.DoesNotExist, AttributeError):
            return False

        return False


class CanAddGroupUserCode(permissions.BasePermission):
    message = 'Permission denied. Cannot add user code.'

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj):
        try:
            if GroupMember.objects.get(group=obj, sesar_user=request.user.sesaruser).auth_group.permissions.filter(codename='add_sesarusercode').exists():
                return True
        except (GroupMember.DoesNotExist, AttributeError):
            return False

        return False


class CanDeleteGroupUserCode(permissions.BasePermission):
    message = 'Permission denied. Cannot delete user code.'

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj):
        try:
            if GroupMember.objects.get(group=obj, sesar_user=request.user.sesaruser).auth_group.permissions.filter(codename='delete_sesarusercode').exists():
                return True
        except (GroupMember.DoesNotExist, AttributeError):
            return False

        return False


class CanTransferGroupSample(permissions.BasePermission):
    message = 'Permission denied. Cannot transfer sample.'

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj):
        try:
            if GroupMember.objects.get(group=obj, sesar_user=request.user.sesaruser).auth_group.permissions.filter(codename='transfer_sample').exists():
                return True
        except (GroupMember.DoesNotExist, AttributeError):
            return False

        return False