from rest_framework import permissions
from sesar_api.models import GroupMember, Permission
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist 


class IsSampleOwner(permissions.BasePermission):
    message = 'Permission denied. This sample is not owned by you.'

    def has_object_permission(self, request, view, obj):
        return obj.cur_owner == request.user.sesaruser


class CanCreateSample(permissions.BasePermission):
    message = 'Permission denied. Cannot create sample.'

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj):
        sample = obj
        user_code = sample.igsn_prefix
        sesar_user = request.user.sesaruser

        # user owns user code
        if user_code.sesar_user == sesar_user:
            return True

        # user owns sample
        if sample.cur_owner == sesar_user:
            return True

        try:
            # user code owned by group that user has add sample permission for
            if user_code.group and GroupMember.objects.get(
                group=user_code.group, 
                sesar_user=sesar_user).auth_group.permissions.filter(codename='add_sample').exists():
                return True
        except (GroupMember.DoesNotExist, AttributeError):
            # continue to next check
            pass

        try:
            # sample owned by group that user has add sample permission for
            if sample.group_owner and GroupMember.objects.get(
                group=sample.group_owner, 
                sesar_user=sesar_user).auth_group.permissions.filter(codename='add_sample').exists():
                return True
        except (GroupMember.DoesNotExist, AttributeError):
            # continue to next check
            pass

        # user is a curator approving a batch registration
        if request.user.is_staff:
            return True

        # check all permissions shared on either user code or directly on sample
        all_permissions = Permission.objects.filter(Q(user_code=user_code) | Q(sample=sample))
        for permission in all_permissions:
            # check both legacy permissions and auth group permissions
            if ((permission.sesar_role and 'C' in permission.sesar_role.sesar_role_name)
                or (permission.auth_group and permission.auth_group.permissions.filter(codename='add_sample').exists())):
                
                # permissions are shared directly with user
                if ((permission.sesar_user and permission.sesar_user == sesar_user)
                    or (permission.orcid_id and permission.orcid_id == sesar_user.orcid)
                    or (permission.geopass_id and permission.orcid_id== sesar_user.geopass_id)):
                    return True

                try:
                    # permissions are shared with group of which user has add sample permission
                    if (permission.group
                    and GroupMember.objects.get(group=permission.group, sesar_user=sesar_user).auth_group.permissions.filter(codename='add_sample').exists()):
                        return True
                except (GroupMember.DoesNotExist, AttributeError):
                    # continue to next check
                    pass
                
                # permissions are shared with a sub group team of which user is a member
                if (permission.group and permission.group.part_of_group
                    and permission.group.members.contains(sesar_user)):
                    return True   

        return False


class CanEditSample(permissions.BasePermission):
    message = 'Permission denied. Cannot edit sample.'

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj):
        sample = obj
        user_code = sample.igsn_prefix
        sesar_user = request.user.sesaruser

        # user owns user code
        if user_code.sesar_user == sesar_user:
            return True

        # user owns sample
        if sample.cur_owner == sesar_user:
            return True

        try:
            # user is an admin of group that owns user code
            if user_code.group and GroupMember.objects.get(
                group=user_code.group, 
                sesar_user=sesar_user).auth_group.permissions.filter(codename='change_sample').exists():
                return True
        except (GroupMember.DoesNotExist, AttributeError):
            # continue to next check
            pass

        try:
            # user is an admin of group that owns sample
            if sample.group_owner and GroupMember.objects.get(
                group=sample.group_owner, 
                sesar_user=sesar_user).auth_group.permissions.filter(codename='change_sample').exists():
                return True
        except (GroupMember.DoesNotExist, AttributeError):
            # continue to next check
            pass

        # user is a curator approving a batch registration
        if request.user.is_staff:
            return True

        # check all permissions shared on either user code or directly on sample
        all_permissions = Permission.objects.filter(Q(user_code=user_code) | Q(sample=sample))
        for permission in all_permissions:
            # check both legacy permissions and auth group permissions
            if ((permission.sesar_role and 'E' in permission.sesar_role.sesar_role_name)
                or (permission.auth_group and permission.auth_group.permissions.filter(codename='change_sample').exists())):
                
                # permissions are shared directly with user
                if ((permission.sesar_user and permission.sesar_user == sesar_user)
                    or (permission.orcid_id and permission.orcid_id == sesar_user.orcid)
                    or (permission.geopass_id and permission.orcid_id== sesar_user.geopass_id)):
                    return True

                try:
                    # permissions are shared with group of which user has change sample permission
                    if (permission.group
                    and GroupMember.objects.get(group=permission.group, sesar_user=sesar_user).auth_group.permissions.filter(codename='change_sample').exists()):
                        return True
                except (GroupMember.DoesNotExist, AttributeError):
                    # continue to next check
                    pass
                
                # permissions are shared with a sub group team of which user is a member
                if (permission.group and permission.group.part_of_group
                    and permission.group.members.contains(sesar_user)):
                    return True

        return False


class CanDeactivateSample(permissions.BasePermission):
    message = 'Permission denied. Cannot deactivate sample.'

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj):
        sample = obj
        user_code = sample.igsn_prefix
        sesar_user = request.user.sesaruser

        # user owns user code
        if user_code.sesar_user == sesar_user:
            return True

        # user owns sample
        if sample.cur_owner == sesar_user:
            return True

        try:
            # user is an admin of group that owns user code
            if user_code.group and GroupMember.objects.get(
                group=user_code.group, 
                sesar_user=sesar_user).auth_group.permissions.filter(codename='deactivate_sample').exists():
                return True
        except (GroupMember.DoesNotExist, AttributeError):
            # continue to next check
            pass


        try:
            # user is an admin of group that owns sample
            if sample.group_owner and GroupMember.objects.get(
                group=sample.group_owner, 
                sesar_user=sesar_user).auth_group.permissions.filter(codename='deactivate_sample').exists():
                return True
        except (GroupMember.DoesNotExist, AttributeError):
            # continue to next check
            pass

        # user is a curator approving a batch registration
        if request.user.is_staff:
            return True

        # check all permissions shared on either user code or directly on sample
        all_permissions = Permission.objects.filter(Q(user_code=user_code) | Q(sample=sample))
        for permission in all_permissions:
            # check both legacy permissions and auth group permissions
            if ((permission.sesar_role and 'D' in permission.sesar_role.sesar_role_name)
                or (permission.auth_group and permission.auth_group.permissions.filter(codename='deactivate_sample').exists())):
                
                # permissions are shared directly with user
                if ((permission.sesar_user and permission.sesar_user == sesar_user)
                    or (permission.orcid_id and permission.orcid_id == sesar_user.orcid)
                    or (permission.geopass_id and permission.orcid_id== sesar_user.geopass_id)):
                    return True

                try:
                    # permissions are shared with group of which user has deactivate sample permission
                    if (permission.group
                    and GroupMember.objects.get(group=permission.group, sesar_user=sesar_user).auth_group.permissions.filter(codename='deactivate_sample').exists()):
                        return True
                except (GroupMember.DoesNotExist, AttributeError):
                    # continue to next check
                    pass
                
                # permissions are shared with a sub group team of which user is a member
                if (permission.group and permission.group.part_of_group
                    and permission.group.members.contains(sesar_user)):
                    return True

        return False