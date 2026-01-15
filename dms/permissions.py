from rest_framework import permissions
from .models import AccessPolicy, UserDepartmentRole

class HasRequiredPermission(permissions.BasePermission):
    """
    Generalized DRF permission that checks if the user has the required permission 
    assigned via AccessPolicy for any of their roles.
    
    Usage in View:
        permission_classes = [HasRequiredPermission]
        required_permission = 'view_procurement'
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        if request.user.is_superuser:
            return True
            
        required_perm = getattr(view, 'required_permission', None)
        
        # 1. Project Ownership check (Grant all if they own the project)
        # We try to find project_id from query params or request payload
        project_id = request.query_params.get('project_id') or request.data.get('project')
        
        from projects.models import Project
        
        # If we have a project context, check it first
        if project_id:
            try:
                # If they own the target project, they have ALL permissions for it.
                if Project.objects.filter(id=project_id, owner_user=request.user).exists():
                    return True
            except (ValueError, TypeError):
                pass
        else:
            # List view or generic request: If they own ANY project, let them through
            # and let the ViewSet's get_queryset handle the scoping.
            if Project.objects.filter(owner_user=request.user).exists():
                return True

        if not required_perm:
            return True
            
        # 2. AccessPolicy check (Departmental Roles)
        # We filter by project_id if provided, otherwise check all roles
        if project_id:
            user_roles = UserDepartmentRole.objects.filter(user=request.user, project_id=project_id)
            for ur in user_roles:
                policy = AccessPolicy.objects.filter(
                    project_id=project_id, 
                    department_id=ur.department_id, 
                    role=ur.role
                ).first()
                if policy and required_perm in policy.permissions:
                    return True
        else:
            # Generic access: Check if they have the permission in ANY project role
            user_roles = UserDepartmentRole.objects.filter(user=request.user)
            for ur in user_roles:
                policy = AccessPolicy.objects.filter(
                    project_id=ur.project_id, 
                    department_id=ur.department_id, 
                    role=ur.role
                ).first()
                if policy and required_perm in policy.permissions:
                    return True
                
        return False

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        owner_user = getattr(obj, 'owner_user', None)
        if owner_user == request.user:
            return True
            
        project = getattr(obj, 'project', None)
        if project and getattr(project, 'owner_user', None) == request.user:
            return True
            
        # Fallback to general permission check
        return self.has_permission(request, view)
