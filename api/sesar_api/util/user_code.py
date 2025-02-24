from sesar_api.models import Team, TeamMember, SesarUserCode, Permission


def get_team_user_codes_with_permission(sesar_user, team, permission):
    user_codes = []
    # check team level permissions
    try:
        if TeamMember.objects.get(team=team, sesar_user=sesar_user).auth_group.permissions.filter(codename=permission).exists():
            # return all team owned user codes
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
                    # if subteam permission on user code exists
                    if subteam_permission.user_code and subteam_permission.auth_group.permissions.filter(codename=permission).exists():
                        user_codes.append(subteam_permission.user_code.user_code)
    except AttributeError:
        # if no subteam level permission set, continue to next check
        pass

    try:
        # check all user permissions granted by team
        for user_permission in Permission.objects.filter(sesar_user=sesar_user, granted_by_team=team):
            # if user permission on user code exists
            if user_permission.user_code and user_permission.auth_group.permissions.filter(codename=permission).exists():
                user_codes.append(user_permission.user_code.user_code)
    except AttributeError:
        # if no user level permission set, continue
        pass

    return user_codes