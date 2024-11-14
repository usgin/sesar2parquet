from sesar_api.models import Group, GroupMember, SesarUserCode, Permission


def get_group_user_codes_with_permission(sesar_user, group, permission):
    user_codes = []
    # check group level permissions
    try:
        if GroupMember.objects.get(group=group, sesar_user=sesar_user).auth_group.permissions.filter(codename=permission).exists():
            # return all group owned user codes
            return 'all'
    except GroupMember.DoesNotExist:
        # user is not a member of group
        return []
    except AttributeError:
        # if no group level permission set, continue to next check
        pass

    # check team level permissions
    try:
        # check all group teams user is a part of
        for team in Group.objects.filter(part_of_group=group):
            if team.members.contains(sesar_user):
                # search all permissions granted to team
                for team_permission in Permission.objects.filter(group=team):
                    # if team permission on user code exists
                    if team_permission.user_code and team_permission.auth_group.permissions.filter(codename=permission).exists():
                        user_codes.append(team_permission.user_code.user_code)
    except AttributeError:
        # if no team level permission set, continue to next check
        pass

    try:
        # check all user permissions granted by group
        for user_permission in Permission.objects.filter(sesar_user=sesar_user, granted_by_group=group):
            # if user permission on user code exists
            if user_permission.user_code and user_permission.auth_group.permissions.filter(codename=permission).exists():
                user_codes.append(user_permission.user_code.user_code)
    except AttributeError:
        # if no user level permission set, continue
        pass

    return user_codes