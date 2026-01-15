from .models import AccessPolicy, Department, UserDepartmentRole
from projects.models import Project

def initialize_project_permissions(project):
    """
    Copies global template AccessPolicies (where project is None) 
    to a specific project.
    """
    templates = AccessPolicy.objects.filter(project__isnull=True)
    
    created_count = 0
    for template in templates:
        # Check if already exists for this project to avoid duplicates
        policy, created = AccessPolicy.objects.get_or_create(
            project=project,
            department=template.department,
            role=template.role,
            defaults={'permissions': template.permissions}
        )
        if created:
            created_count += 1
        else:
            # Optionally update if it already exists? 
            # User said "generic seed the owner can change", 
            # so we only seed if missing.
            pass
            
    return created_count

def seed_global_templates():
    """
    Initializes the global AccessPolicy templates if they don't exist.
    """
    departments = Department.objects.all()
    roles = ['HOD', 'OFFICER', 'ADMIN']
    
    default_perms = {
        'HOD': ['view_dashboard', 'view_tasks', 'submit_tasks', 'approve_tasks', 'manage_team', 'view_team'],
        'OFFICER': ['view_dashboard', 'view_tasks', 'submit_tasks', 'view_team'],
        'ADMIN': ['view_dashboard', 'view_tasks', 'manage_team', 'view_team']
    }
    
    # Specific overrides for certain departments
    overrides = {
        'PROCUREMENT': {
            'HOD': ['view_dashboard', 'view_tasks', 'submit_tasks', 'approve_tasks', 'manage_team', 'view_team', 'view_procurement', 'manage_procurement'],
            'OFFICER': ['view_dashboard', 'view_tasks', 'submit_tasks', 'view_team', 'view_procurement'],
        },
        'HR': {
            'HOD': ['view_dashboard', 'view_tasks', 'submit_tasks', 'approve_tasks', 'manage_team', 'view_team', 'view_hr', 'manage_hr'],
            'OFFICER': ['view_dashboard', 'view_tasks', 'submit_tasks', 'view_team', 'view_hr'],
        }
    }

    created_count = 0
    for dept in departments:
        for role in roles:
            perms = overrides.get(dept.code, {}).get(role, default_perms.get(role, []))
            
            policy, created = AccessPolicy.objects.get_or_create(
                project=None,
                department=dept,
                role=role,
                defaults={'permissions': perms}
            )
            if created:
                created_count += 1
                
    return created_count
