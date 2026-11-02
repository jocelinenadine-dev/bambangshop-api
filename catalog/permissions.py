"""Custom authorization policies for catalog API."""

from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """Permission policy allowing read access to all, but write access only to owners."""

    def has_object_permission(self, request, view, obj) -> bool:
        """Check whether request is allowed for a specific model instance."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == request.user
