"""Permission classes."""

from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    """Allow only user_type=admin users (NOT the Django is_staff flag)."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.user_type == "admin"
        )
