from rest_framework import permissions
from sesar_api.models import GroupMember, Permission


class BaseUserCodePermission(permissions.BasePermission):
    """
    Base permission for handling common logic for user code permissions.
    """
    def user_owns_user_code(self, user_code, sesar_user):
        return user_code.sesar_user == sesar_user

    def user_has_group_permission(self, group, sesar_user, codename):
        try:
            return (
                group and
                GroupMember.objects.get(group=group, sesar_user=sesar_user)
                .auth_group.permissions.filter(codename=codename)
                .exists()
            )
        except (GroupMember.DoesNotExist, AttributeError):
            return False

    def user_has_shared_permission(self, user_code, sesar_user, role_check, codename):
        all_permissions = Permission.objects.filter(user_code=user_code)

        for permission in all_permissions:
            # Check legacy roles or auth group permissions
            if (
                (permission.sesar_role and role_check in permission.sesar_role.sesar_role_name) or
                (permission.auth_group and permission.auth_group.permissions.filter(codename=codename).exists())
            ):
                # Direct user matches
                if (
                    (permission.sesar_user and permission.sesar_user == sesar_user) or
                    (permission.orcid_id and permission.orcid_id == sesar_user.orcid) or
                    (permission.geopass_id and permission.orcid_id == sesar_user.geopass_id)
                ):
                    return True

                # Permissions shared with user's group
                if self.user_has_group_permission(permission.group, sesar_user, codename):
                    return True

                # Permissions shared with subgroup teams
                if (
                    permission.group and permission.group.part_of_group and
                    permission.group.members.contains(sesar_user)
                ):
                    return True

        return False

    def has_permission_logic(self, request, obj, codename, role_check):
        user_code = obj
        sesar_user = request.user.sesaruser

        # User ownership checks
        if self.user_owns_user_code(user_code, sesar_user):
            return True

        # Group permission checks
        if self.user_has_group_permission(user_code.group, sesar_user, codename):
            return True

        # Staff permission check
        if request.user.is_staff:
            return True

        # Shared permissions
        if self.user_has_shared_permission(user_code, sesar_user, role_check, codename):
            return True

        return False


class IsUserCodeOwner(permissions.BasePermission):
    message = 'Permission denied. This user code is not owned by you or your group'

    def __init__(self, group=None):
        self.group = group

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj):
        # user code is owned by request user or passed in group object
        return (obj.sesar_user == request.user.sesaruser 
            or (obj.group is not None and obj.group == self.group))



class CanCreateSampleOnUserCode(BaseUserCodePermission):
    message = 'Permission denied. Cannot create samples on user code.'

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return self.has_permission_logic(request, obj, codename='add_sample', role_check='C')


class CanEditSampleOnUserCode(BaseUserCodePermission):
    message = 'Permission denied. Cannot edit samples on user code.'

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return self.has_permission_logic(request, obj, codename='change_sample', role_check='E')


class CanDeactivateSampleOnUserCode(BaseUserCodePermission):
    message = 'Permission denied. Cannot deactivate samples on user code.'

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return self.has_permission_logic(request, obj, codename='deactivate_sample', role_check='D')
