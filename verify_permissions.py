import os
import django
import sys
import json

# Setup Django environment
sys.path.append('/home/mughal41/PycharmProjects/djangoProjects/PIC_ERP_Backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from dms.models import Project, Department, UserDepartmentRole, AccessPolicy
from auth_app.views import get_user_data_response

User = get_user_model()

def verify_permissions():
    print("--- User Permission Verification Script ---")
    
    # 1. Setup Test Data
    user, _ = User.objects.get_or_create(username='test_user_perm_fix', email='test@example.com')
    
    project_a, _ = Project.objects.get_or_create(code='PRJ-A', name='Project A')
    project_b, _ = Project.objects.get_or_create(code='PRJ-B', name='Project B')
    
    dept, _ = Department.objects.get_or_create(code='DEPT-X', name='Department X')
    
    # Create Policies
    # Project A: Grants 'view_planning'
    p1, _ = AccessPolicy.objects.get_or_create(
        project=project_a, department=dept, role='OFFICER',
        defaults={'permissions': ['view_planning']}
    )
    p1.permissions = ['view_planning']
    p1.save()

    # Project B: Grants NOTHING (or different perm)
    p2, _ = AccessPolicy.objects.get_or_create(
        project=project_b, department=dept, role='OFFICER',
        defaults={'permissions': ['other_perm']}
    )
    p2.permissions = [] # Explicitly empty for test
    p2.save()
    
    # Assign Role in Project A
    UserDepartmentRole.objects.filter(user=user).delete()
    UserDepartmentRole.objects.create(user=user, department=dept, project=project_a, role='OFFICER')
    
    # 2. Test Response
    print("Fetching user data...")
    response = get_user_data_response(user)
    
    project_perms = response['user'].get('project_permissions', {})
    print(f"Project Permissions: {json.dumps(project_perms, indent=2)}")
    
    # 3. Assertions
    # Project A should have 'view_planning'
    if 'view_planning' in project_perms.get(str(project_a.id), []):
        print("PASS: Project A has 'view_planning'")
    else:
        print(f"FAIL: Project A missing 'view_planning'. Got: {project_perms.get(str(project_a.id))}")

    # Project B should NOT exist or be empty (since no role assigned there)
    if str(project_b.id) not in project_perms:
        print("PASS: Project B correctly has no permissions (no role assigned)")
    else:
        print(f"FAIL: Project B has unexpected permissions: {project_perms.get(str(project_b.id))}")
        
    print("--- Verification Complete ---")

if __name__ == "__main__":
    try:
        verify_permissions()
    except Exception as e:
        print(e)
