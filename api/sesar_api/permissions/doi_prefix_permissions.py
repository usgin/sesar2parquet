from rest_framework import permissions
from sesar_api.models import Team, TeamMember


class BaseDoiPrefixPermission(permissions.BasePermission):
    """
    Base permission for handling common logic for sample permissions.
    """
    def user_has_team_permission(self, teams, sesar_user, codename):
        try:
            if teams:
                for team in teams:
                    if (TeamMember.objects.get(team=team, sesar_user=sesar_user)
                            .auth_group.permissions.filter(codename=codename)
                            .exists()
                        ):
                        return True
        except (TeamMember.DoesNotExist, AttributeError):
            return False


    def has_permission_logic(self, request, obj, codename, role_check):
        doi_prefix = obj
        sesar_user = request.user.sesaruser

        teams = Team.objects.filter(doi_prefix=doi_prefix)

        # Team permission checks
        if self.user_has_team_permission(teams, sesar_user, codename):
            return True

        # Staff permission check
        if request.user.is_staff:
            return True

        return False


class CanCreateSampleOnDoiPrefix(BaseDoiPrefixPermission):
    message = 'Permission denied. Cannot create sample on DOI prefix.'

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return self.has_permission_logic(request, obj, codename='add_sample', role_check='C')