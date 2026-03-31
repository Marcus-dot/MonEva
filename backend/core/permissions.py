from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    """True if the user's role has is_admin=True, or has the manage_roles permission."""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_admin_user:
            return True
        return request.user.has_permission('manage_roles')

class IsProjectManager(permissions.BasePermission):
    """True if the user is an admin or has the project_management permission."""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_admin_user:
            return True
        return request.user.has_permission('manage_projects')

class IsFinance(permissions.BasePermission):
    """True if the user is an admin or has the finance permission."""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_admin_user:
            return True
        return request.user.has_permission('manage_finance')

class IsInspector(permissions.BasePermission):
    """True if the user is an admin or has the inspection permission."""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_admin_user:
            return True
        return request.user.has_permission('manage_inspections')

class ReadOnly(permissions.BasePermission):
    """Allow read-only access"""
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS

class HasPermission(permissions.BasePermission):
    """
    Custom permission to check if user has a specific permission code.
    Usage: Set permission_required attribute on the view.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Get the required permission from the view
        permission_code = getattr(view, 'permission_required', None)
        if not permission_code:
            return True  # No specific permission required
        
        return request.user.has_permission(permission_code)
