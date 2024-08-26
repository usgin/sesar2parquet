from rest_framework import permissions


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