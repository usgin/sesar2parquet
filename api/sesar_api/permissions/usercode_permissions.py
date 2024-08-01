from rest_framework import permissions


class IsUserCodeOwner(permissions.BasePermission):
    message = 'Permission denied. This user code is not owned by you or your organization'

    def __init__(self, organization=None):
        self.organization = organization

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj):
        # user code is owned by request user or passed in organization object
        return (obj.sesar_user == request.user.sesaruser 
            or (obj.organization is not None and obj.organization == self.organization))