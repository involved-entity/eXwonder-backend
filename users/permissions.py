from rest_framework import permissions


class UserPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action in ('create', 'login', 'two_factor_authentication'):
            return True
        return bool(request.user and request.user.is_authenticated)
