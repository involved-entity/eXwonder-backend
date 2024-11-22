from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user == obj.author


class IsOwnerOrCreateOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if view.action in ("list", "destroy"):
            return request.user == obj.owner
        return True
