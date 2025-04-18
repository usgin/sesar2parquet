from sesar_api.models import Team, TeamMember, Permission


def get_team_sesar_codes_with_permission(sesar_user, team, permission):
    sesar_codes = []
    # check team level permissions
    try:
        if TeamMember.objects.get(team=team, sesar_user=sesar_user).auth_group.permissions.filter(codename=permission).exists():
            # return all team owned Sesar codes
            return 'all'
    except TeamMember.DoesNotExist:
        # user is not a member of team
        return []
    except AttributeError:
        # if no team level permission set, continue to next check
        pass

    # check subteam level permissions
    try:
        # check all subteam user is a part of
        for subteam in Team.objects.filter(part_of_team=subteam):
            if subteam.members.contains(sesar_user):
                # search all permissions granted to subteam
                for subteam_permission in Permission.objects.filter(team=subteam):
                    # if subteam permission on Sesar code exists
                    if subteam_permission.sesar_code and subteam_permission.auth_group.permissions.filter(codename=permission).exists():
                        sesar_codes.append(subteam_permission.sesar_code.sesar_code)
    except AttributeError:
        # if no subteam level permission set, continue to next check
        pass

    try:
        # check all user permissions granted by team
        for user_permission in Permission.objects.filter(sesar_user=sesar_user, granted_by_team=team):
            # if user permission on Sesar code exists
            if user_permission.sesar_code and user_permission.auth_group.permissions.filter(codename=permission).exists():
                sesar_codes.append(user_permission.sesar_code.sesar_code)
    except AttributeError:
        # if no user level permission set, continue
        pass

    return sesar_codes