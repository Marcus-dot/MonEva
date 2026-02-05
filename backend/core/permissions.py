from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    """Check if user has Administrator role or manage_roles permission"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        # Check if user has Administrator role
        if request.user.role and request.user.role.name == 'Administrator':
            return True
        # Or check if user has manage_roles permission
        return request.user.has_permission('manage_roles')

class IsProjectManager(permissions.BasePermission):
    """Check if user has Project Manager role or higher"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.role:
            return request.user.role.name in ['Administrator', 'Project Manager']
        return False

class IsFinance(permissions.BasePermission):
    """Check if user has finance permissions"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        # Check for Administrator or Project Manager roles (they have finance perms)
        if request.user.role:
            return request.user.role.name in ['Administrator', 'Project Manager']
        return False

class IsInspector(permissions.BasePermission):
    """Check if user has inspection permissions"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.role:
            return request.user.role.name in ['Administrator', 'Project Manager', 'Evaluator']
        return False

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
