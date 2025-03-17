from rest_framework import permissions
from sesar_api.models import TeamMember, Permission
from django.contrib.auth.models import Group as AuthGroup
from django.db.models import Q


class CanGrantSamplePermission(permissions.BasePermission):
    message = 'Permission denied. Cannot grant permission on sample.'

    def __init__(self, team=None, permissions_to_grant=None):
        # for the case where permissions were originally shared to a team, but the sample is not owned by the team
        # the permissions should only be shared within that team and within the bounds of the original granted permissions
        self.team = team
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

        try:
            # user is an admin of team that owns sample
            if sample.team_owner and TeamMember.objects.get(
                team=sample.team_owner, 
                sesar_user=sesar_user).auth_group.permissions.filter(codename='add_permission').exists():
                return True
        except (TeamMember.DoesNotExist, AttributeError):
            # continue to next check
            pass

        try:
            # if case of sharing permissions within a team with granted permissions
            if self.team and TeamMember.objects.get(
                team=self.team, 
                sesar_user=sesar_user).auth_group.permissions.filter(codename='add_permission').exists():
                # get the original permission granted to the team
                permission = Permission.objects.get(sample=sample, team=self.team)
                if permission and permission.auth_group:
                    # check if team has all permissions that are attempting to be shared
                    for auth_permission in self.permissions_to_grant.permissions.all():
                        if not permission.auth_group.permissions.filter(codename=auth_permission.codename).exists():
                            # return false if a given permission does not exist
                            return False
                    return True
        except (TeamMember.DoesNotExist, Permission.DoesNotExist, AttributeError):
            # continue to next check
            pass

        return False


class CanGrantSesarCodePermission(permissions.BasePermission):
    message = 'Permission denied. Cannot grant permission on sesar code.'

    def __init__(self, team=None, permissions_to_grant=None):
        # for the case where permissions were originally shared to a team, but the sesar code is not owned by the team
        # the permissions should only be shared within that team and within the bounds of the original granted permissions
        self.team = team
        self.permissions_to_grant = AuthGroup.objects.filter(name=permissions_to_grant).first()

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj):
        sesar_code = obj
        sesar_user = request.user.sesaruser

        # user owns sesar code
        if sesar_code.sesar_user == sesar_user:
            return True

        try:
            # user is an admin of team that owns sesar code
            if sesar_code.team and TeamMember.objects.get(
                team=sesar_code.team, 
                sesar_user=sesar_user).auth_group.permissions.filter(codename='add_permission').exists():
                return True
        except (TeamMember.DoesNotExist, AttributeError):
            # continue to next check
            pass

        try:
            # if case of sharing permissions within a team with granted permissions
            if self.team and TeamMember.objects.get(
                team=self.team, 
                sesar_user=sesar_user).auth_group.permissions.filter(codename='add_permission').exists():
                # get the original permission granted to the team
                permission = Permission.objects.get(sesar_code=sesar_code, team=self.team)
                if permission and permission.auth_group:
                    # check if team has all permissions that are attempting to be shared
                    for auth_permission in self.permissions_to_grant.permissions.all():
                        if not permission.auth_group.permissions.filter(codename=auth_permission.codename).exists():
                            # return false if a given permission does not exist
                            return False
                    return True
        except (TeamMember.DoesNotExist, Permission.DoesNotExist, AttributeError):
            # continue to next check
            pass

        return False


class CanEditPermission(permissions.BasePermission):
    message = 'Permission denied. Cannot make changes to this permission.'

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj):
        permission = obj
        sesar_user = request.user.sesaruser

        # user owns sesar code
        if permission.sesar_code and permission.sesar_code.sesar_user == sesar_user:
            return True

        # user owns sample
        if permission.sample and permission.sample.cur_owner == sesar_user:
            return True

        try:
            # user is an admin of team that granted permission
            if permission.granted_by_team and TeamMember.objects.get(
                team=permission.granted_by_team, 
                sesar_user=sesar_user).auth_group.permissions.filter(codename='change_permission').exists():
                return True
        except (TeamMember.DoesNotExist, Permission.DoesNotExist,  AttributeError):
            # continue to next check
            pass

        return False