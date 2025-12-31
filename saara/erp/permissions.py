from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdmin(BasePermission):
    """
    Permission class that only allows admin users full access.
    """
    message = "Only administrators can perform this action."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return getattr(request.user, 'role', None) == 'admin'


class IsAdminOrReadOnly(BasePermission):
    """
    Permission class that allows:
    - Admin: Full access (CRUD)
    - Others: Read-only access
    """
    message = "Only administrators can modify this resource."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Allow read-only for all authenticated users
        if request.method in SAFE_METHODS:
            return True
        
        # Only admin can modify
        return getattr(request.user, 'role', None) == 'admin'


class IsAdminOrTeacher(BasePermission):
    """
    Permission class that allows:
    - Admin: Full access (CRUD)
    - Teacher/Faculty: Full access (CRUD)
    - Others: Read-only access
    """
    message = "Only administrators and teachers can modify this resource."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Allow read-only for all authenticated users
        if request.method in SAFE_METHODS:
            return True
        
        # Admin and faculty can modify
        user_role = getattr(request.user, 'role', None)
        return user_role in ['admin', 'faculty']


class IsAdminOrTeacherForWrite(BasePermission):
    """
    Permission class for attendance, assignments, and results:
    - Admin: Full access (CRUD)
    - Teacher/Faculty: Can create, update (but check object-level for own resources)
    - Students: Read-only access
    """
    message = "Only administrators and teachers can modify this resource."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Allow read-only for all authenticated users
        if request.method in SAFE_METHODS:
            return True
        
        # Admin and faculty can modify
        user_role = getattr(request.user, 'role', None)
        return user_role in ['admin', 'faculty']
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Allow read-only for all authenticated users
        if request.method in SAFE_METHODS:
            return True
        
        user_role = getattr(request.user, 'role', None)
        
        # Admin has full access
        if user_role == 'admin':
            return True
        
        # Faculty can modify
        if user_role == 'faculty':
            return True
        
        return False


class IsOwnerOrAdmin(BasePermission):
    """
    Permission class that allows:
    - Admin: Full access
    - Owner: Access to their own data
    """
    message = "You can only access your own data."
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        user_role = getattr(request.user, 'role', None)
        
        # Admin has full access
        if user_role == 'admin':
            return True
        
        # Check if user owns the object
        if hasattr(obj, 'user') and obj.user:
            return obj.user.user_id == request.user.user_id
        
        if hasattr(obj, 'student') and obj.student:
            if hasattr(obj.student, 'user') and obj.student.user:
                return obj.student.user.user_id == request.user.user_id
        
        return False
