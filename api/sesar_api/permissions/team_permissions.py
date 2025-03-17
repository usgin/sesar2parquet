from rest_framework import permissions
from sesar_api.models import TeamMember


class IsTeamOwner(permissions.BasePermission):
    message = 'Permission denied. This team is not owned by you.'

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user.sesaruser


class CanAddTeamMember(permissions.BasePermission):
    message = 'Permission denied. Cannot add team member.'

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj):
        try:
            if TeamMember.objects.get(team=obj, sesar_user=request.user.sesaruser).auth_group.permissions.filter(codename='add_teammember').exists():
                return True
        except (TeamMember.DoesNotExist, AttributeError):
            return False

        return False

class CanChangeTeamMember(permissions.BasePermission):
    message = 'Permission denied. Cannot change team member.'

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj):
        try:
            if TeamMember.objects.get(team=obj, sesar_user=request.user.sesaruser).auth_group.permissions.filter(codename='change_teammember').exists():
                return True
        except (TeamMember.DoesNotExist, AttributeError):
            return False

        return False

class CanDeleteTeamMember(permissions.BasePermission):
    message = 'Permission denied. Cannot delete team member.'

    def __init__(self, member=None):
        # for the case where permissions were originally shared to a team, but the Sesar code is not owned by the team
        # the permissions should only be shared within that team and within the bounds of the original granted permissions
        self.member = member

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj):
        try:
            if TeamMember.objects.get(team=obj, sesar_user=request.user.sesaruser).auth_group.permissions.filter(codename='delete_teammember').exists():
                return True
            if request.user.sesaruser == self.member and obj.owner != self.member: # user can remove themselves
                return True
        except (TeamMember.DoesNotExist, AttributeError):
            return False

        return False

class CanAddTeam(permissions.BasePermission):
    message = 'Permission denied. Cannot add team.'

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj):
        try:
            if TeamMember.objects.get(team=obj, sesar_user=request.user.sesaruser).auth_group.permissions.filter(codename='add_team').exists():
                return True
        except (TeamMember.DoesNotExist, AttributeError):
            return False

        return False

class CanChangeTeam(permissions.BasePermission):
    message = 'Permission denied. Cannot change team.'

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj):
        try:
            if TeamMember.objects.get(team=obj, sesar_user=request.user.sesaruser).auth_group.permissions.filter(codename='change_team').exists():
                return True
        except (TeamMember.DoesNotExist, AttributeError):
            return False

        return False

class CanDeleteTeam(permissions.BasePermission):
    message = 'Permission denied. Cannot delete team.'

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj):
        try:
            if TeamMember.objects.get(team=obj, sesar_user=request.user.sesaruser).auth_group.permissions.filter(codename='delete_team').exists():
                return True
        except (TeamMember.DoesNotExist, AttributeError):
            return False

        return False


class CanViewTeamSamples(permissions.BasePermission):
    message = 'Permission denied. Cannot view team samples.'

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj):
        try:
            if TeamMember.objects.get(team=obj, sesar_user=request.user.sesaruser).auth_group.permissions.filter(codename='view_sample').exists():
                return True
        except (TeamMember.DoesNotExist, AttributeError):
            return False

        return False


class CanAddTeamSesarCode(permissions.BasePermission):
    message = 'Permission denied. Cannot add Sesar code.'

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj):
        try:
            if TeamMember.objects.get(team=obj, sesar_user=request.user.sesaruser).auth_group.permissions.filter(codename='add_sesarcode').exists():
                return True
        except (TeamMember.DoesNotExist, AttributeError):
            return False

        return False


class CanDeleteTeamSesarCode(permissions.BasePermission):
    message = 'Permission denied. Cannot delete Sesar code.'

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj):
        try:
            if TeamMember.objects.get(team=obj, sesar_user=request.user.sesaruser).auth_group.permissions.filter(codename='delete_sesarcode').exists():
                return True
        except (TeamMember.DoesNotExist, AttributeError):
            return False

        return False


class CanTransferTeamSample(permissions.BasePermission):
    message = 'Permission denied. Cannot transfer sample.'

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj):
        try:
            if TeamMember.objects.get(team=obj, sesar_user=request.user.sesaruser).auth_group.permissions.filter(codename='transfer_sample').exists():
                return True
        except (TeamMember.DoesNotExist, AttributeError):
            return False

        return False