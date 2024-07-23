from rest_framework import permissions
from sesar_api.models import OrganizationMember, SamplePermission
from django.db.models import Q


class IsSampleOwner(permissions.BasePermission):
    message = 'Permission denied. This sample is not owned by you.'

    def has_object_permission(self, request, view, obj):
        return obj.cur_owner == request.user.sesar_user


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

        # check all permissions shared on either user code or directly on sample
        all_permissions = SamplePermission.objects.filter(Q(user_code=user_code) | Q(sample=sample))
        for permission in all_permissions:
            # check both legacy permissions and auth group permissions
            if ('C' in permission.sesar_role.sesar_role_name
                or (permission.auth_group and permission.auth_group.permissions.filter(codename='add_sample').exists())):
                
                # permissions are shared directly with user
                if (permission.sesar_user == sesar_user
                    or permission.orcid_id == sesar_user.orcid
                    or permission.geopass_id == sesar_user.geopass_id):
                    return True
                
                # permissions are shared with an organization team of which user is a member
                if (permission.organization_team 
                    and permission.organization_team.members.filter(sesar_user=sesar_user).exists()):
                    return True

                # permissions are shared with organization of which user is an admin
                if (permission.organization 
                and permission.organization.members.filter(is_admin=True).contains(sesar_user)):
                    return True

        # user is an admin of organization that owns user code
        if OrganizationMember.objects.filter(
            organization=user_code.organization, 
            sesar_user=sesar_user, 
            is_admin=True).exists():
            return True


        # user is a curator approving a batch registration
        if request.user.is_staff:
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

        # check all permissions shared on either user code or directly on sample
        all_permissions = SamplePermission.objects.filter(Q(user_code=user_code) | Q(sample=sample))
        for permission in all_permissions:
            # check both legacy permissions and auth group permissions
            if ('E' in permission.sesar_role.sesar_role_name
                or (permission.auth_group and permission.auth_group.permissions.filter(codename='change_sample').exists())):
                
                # permissions are shared directly with user
                if (permission.sesar_user == sesar_user
                    or permission.orcid_id == sesar_user.orcid
                    or permission.geopass_id == sesar_user.geopass_id):
                    return True
                
                # permissions are shared with an organization team of which user is a member
                if (permission.organization_team 
                    and permission.organization_team.members.filter(sesar_user=sesar_user).exists()):
                    return True

                # permissions are shared with organization of which user is an admin
                if (permission.organization 
                and permission.organization.members.filter(is_admin=True).contains(sesar_user)):
                    return True

        # user is an admin of organization that owns user code
        if OrganizationMember.objects.filter(
            organization=user_code.organization, 
            sesar_user=sesar_user, 
            is_admin=True).exists():
            return True


        # user is a curator approving a batch registration
        if request.user.is_staff:
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

        # check all permissions shared on either user code or directly on sample
        all_permissions = SamplePermission.objects.filter(Q(user_code=user_code) | Q(sample=sample))
        for permission in all_permissions:
            # check both legacy permissions and auth group permissions
            if ('D' in permission.sesar_role.sesar_role_name
                or (permission.auth_group and permission.auth_group.permissions.filter(codename='deactivate_sample').exists())):
                
                # permissions are shared directly with user
                if (permission.sesar_user == sesar_user
                    or permission.orcid_id == sesar_user.orcid
                    or permission.geopass_id == sesar_user.geopass_id):
                    return True
                
                # permissions are shared with an organization team of which user is a member
                if (permission.organization_team 
                    and permission.organization_team.members.filter(sesar_user=sesar_user).exists()):
                    return True

                # permissions are shared with organization of which user is an admin
                if (permission.organization 
                and permission.organization.members.filter(is_admin=True).contains(sesar_user)):
                    return True

        # user is an admin of organization that owns user code
        if OrganizationMember.objects.filter(
            organization=user_code.organization, 
            sesar_user=sesar_user, 
            is_admin=True).exists():
            return True


        # user is a curator approving a batch registration
        if request.user.is_staff:
            return True

        return False