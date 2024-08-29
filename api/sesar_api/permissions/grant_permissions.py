from rest_framework import permissions
from sesar_api.models import GroupMember, Permission
from django.contrib.auth.models import Group as AuthGroup
from django.db.models import Q


class CanGrantSamplePermission(permissions.BasePermission):
    message = 'Permission denied. Cannot grant permission on sample.'

    def __init__(self, group=None, permissions_to_grant=None):
        # for the case where permissions were originally shared to a group, but the sample is not owned by the group
        # the permissions should only be shared within that group and within the bounds of the original granted permissions
        self.group = group
        self.permissions_to_grant = AuthGroup.objects.filter(name=permissions_to_grant).first()

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj):
        sample = obj
        sesar_user = request.user.sesaruser

        # user owns sample
        if sample.cur_owner == sesar_user:
            return True

        # user is an admin of group that owns sample
        if sample.group_owner and GroupMember.objects.filter(
            group=sample.group_owner, 
            sesar_user=sesar_user, 
            is_admin=True).exists():
            return True

        # if case of sharing permissions within a group with granted permissions
        if self.group and GroupMember.objects.filter(
            group=self.group, 
            sesar_user=sesar_user, 
            is_admin=True).exists():
            # get the original permission granted to the group
            permission = Permission.objects.get(sample=sample, group=self.group)
            if permission and permission.auth_group:
                # check if group has all permissions that are attempting to be shared
                for auth_permission in self.permissions_to_grant.permissions.all():
                    if not permission.auth_group.permissions.filter(codename=auth_permission.codename).exists():
                        # return false if a given permission does not exist
                        return False
                return True

        return False


class CanGrantUserCodePermission(permissions.BasePermission):
    message = 'Permission denied. Cannot grant permission on user code.'

    def __init__(self, group=None, permissions_to_grant=None):
        # for the case where permissions were originally shared to a group, but the user code is not owned by the group
        # the permissions should only be shared within that group and within the bounds of the original granted permissions
        self.group = group
        self.permissions_to_grant = AuthGroup.objects.filter(name=permissions_to_grant).first()

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj):
        user_code = obj
        sesar_user = request.user.sesaruser

        # user owns user code
        if user_code.sesar_user == sesar_user:
            return True

        # user is an admin of group that owns user code
        if user_code.group and GroupMember.objects.filter(
            group=user_code.group, 
            sesar_user=sesar_user, 
            is_admin=True).exists():
            return True

        # if case of sharing permissions within a group with granted permissions
        if self.group and GroupMember.objects.filter(
            group=self.group, 
            sesar_user=sesar_user, 
            is_admin=True).exists():
            # get the original permission granted to the group
            permission = Permission.objects.get(user_code=user_code, group=self.group)
            if permission and permission.auth_group:
                # check if group has all permissions that are attempting to be shared
                for auth_permission in self.permissions_to_grant.permissions.all():
                    if not permission.auth_group.permissions.filter(codename=auth_permission.codename).exists():
                        # return false if a given permission does not exist
                        return False
                return True

        return False


class CanEditPermission(permissions.BasePermission):
    message = 'Permission denied. Cannot make changes to this permission.'

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj):
        permission = obj
        sesar_user = request.user.sesaruser

        # user owns user code
        if permission.user_code and permission.user_code.sesar_user == sesar_user:
            return True

        # user owns sample
        if permission.sample and permission.sample.cur_owner == sesar_user:
            return True

        # user is an admin of group that granted permission
        if permission.granted_by_group and GroupMember.objects.filter(
            group=permission.granted_by_group, 
            sesar_user=sesar_user, 
            is_admin=True).exists():
            return True

        return False