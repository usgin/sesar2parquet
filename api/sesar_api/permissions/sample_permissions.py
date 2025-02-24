from rest_framework import permissions
from sesar_api.models import TeamMember, Permission


class BaseSamplePermission(permissions.BasePermission):
    """
    Base permission for handling common logic for sample permissions.
    """
    def user_owns_sample(self, sample, sesar_user):
        return sample.cur_owner == sesar_user

    def user_has_team_permission(self, team, sesar_user, codename):
        try:
            return (
                team and
                TeamMember.objects.get(team=team, sesar_user=sesar_user)
                .auth_group.permissions.filter(codename=codename)
                .exists()
            )
        except (TeamMember.DoesNotExist, AttributeError):
            return False

    def user_has_shared_permission(self, sample, sesar_user, role_check, codename):
        all_permissions = Permission.objects.filter(sample=sample)

        for permission in all_permissions:
            # Check legacy roles or auth team permissions
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

                # Permissions shared with user's team
                if self.user_has_team_permission(permission.team, sesar_user, codename):
                    return True

                # Permissions shared with subteam teams
                if (
                    permission.team and permission.team.part_of_team and
                    permission.team.members.contains(sesar_user)
                ):
                    return True

        return False

    def has_permission_logic(self, request, obj, codename, role_check):
        sample = obj
        sesar_user = request.user.sesaruser

        # User ownership checks
        if self.user_owns_sample(sample, sesar_user):
            return True

        # Team permission checks
        if self.user_has_team_permission(sample.team_owner, sesar_user, codename):
            return True

        # Staff permission check
        if request.user.is_staff:
            return True

        # Shared permissions
        if self.user_has_shared_permission(sample, sesar_user, role_check, codename):
            return True

        return False


class IsSampleOwner(BaseSamplePermission):
    message = 'Permission denied. This sample is not owned by you.'

    def has_object_permission(self, request, view, obj):
        return obj.cur_owner == request.user.sesaruser


class CanCreateSample(BaseSamplePermission):
    message = 'Permission denied. Cannot create sample.'

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return self.has_permission_logic(request, obj, codename='add_sample', role_check='C')


class CanEditSample(BaseSamplePermission):
    message = 'Permission denied. Cannot edit sample.'

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return self.has_permission_logic(request, obj, codename='change_sample', role_check='E')


class CanDeactivateSample(BaseSamplePermission):
    message = 'Permission denied. Cannot deactivate sample.'

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return self.has_permission_logic(request, obj, codename='deactivate_sample', role_check='D')
