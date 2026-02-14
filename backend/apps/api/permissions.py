"""
Custom permissions for Gastrotech API.
"""

from rest_framework.permissions import BasePermission


class IsAdminOrEditor(BasePermission):
    """
    Permission that allows access to authenticated users with admin or editor role.
    
    Used for /api/v1/admin/* endpoints.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has admin or editor role
        user_role = getattr(request.user, "role", None)
        return user_role in ("admin", "editor")
