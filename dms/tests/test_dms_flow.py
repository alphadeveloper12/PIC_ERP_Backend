import os
import django
import sys
import time

sys.path.append('/home/ebony/PycharmProjects/PIC_ERP_Backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from projects.models import Project, Company
from dms.models import Department, UserDepartmentRole, Task, WorkflowStep
from django.utils import timezone

User = get_user_model()

def test_dms_flow():
    print("--- Starting DMS Flow Test ---")
    
    # 1. Setup Company and Project
    # Company requires name and code
    company_name = "Test Company DMS"
    company_code = "COMP-DMS"
    if Company.objects.filter(name=company_name).exists():
        company = Company.objects.get(name=company_name)
    else:
        company = Company.objects.create(name=company_name, code=company_code, address='Test Address')
        
    project, _ = Project.objects.get_or_create(
        code="DMS-TEST-001", 
        defaults={'name': "DMS Test Project", 'company': company}
    )
    print(f"Project: {project}")

    # 2. Setup Users and Departments
    # Ensure departments exist (from import)
    try:
        qs_dept = Department.objects.get(code='QS')
        # Attempt to find bidder dept, code might vary due to uniqueness fix
        # Let's search by name
        bidders_dept = Department.objects.filter(name__icontains='Bidder').first()
        if not bidders_dept:
             bidders_dept, _ = Department.objects.get_or_create(code='BID', name='Bidders')
    except Department.DoesNotExist:
        # Fallback
        qs_dept, _ = Department.objects.get_or_create(code='QS', name='QS')
        bidders_dept, _ = Department.objects.get_or_create(code='BID', name='Bidders')
        
    qs_user, _ = User.objects.get_or_create(username='qs_head', defaults={'email': 'qs@test.com'})
    bidder_user, _ = User.objects.get_or_create(username='bidder_test', defaults={'email': 'bid@test.com'})
    
    UserDepartmentRole.objects.get_or_create(user=qs_user, department=qs_dept, role='HOD')
    UserDepartmentRole.objects.get_or_create(user=bidder_user, department=bidders_dept, role='OFFICER')
    
    print(f"Users setup: QS={qs_user}, Bidder={bidder_user}")

    # 3. Manually create the first task 
    # Find Step 2.1
    step_2_1 = WorkflowStep.objects.filter(sequence_id='2.1').first()
    if not step_2_1:
        print("Error: Step 2.1 not found. Ensure import ran successfully.")
        return

    # Clean up old tasks for this project if any
    Task.objects.filter(project=project).delete()

    task_1 = Task.objects.create(
        project=project,
        workflow_step=step_2_1,
        status='PENDING',
        assigned_to=qs_user 
    )
    print(f"Created Task 1: {task_1} (Status: {task_1.status})")

    # 4. Simulate Approval of Task 1
    # This should trigger the signal
    print("Approving Task 1...")
    task_1.status = 'APPROVED'
    task_1.completed_at = timezone.now()
    task_1.save()
    
    # Wait a moment for signal (synchronous, but good practice)
    time.sleep(1)
    
    # 5. Verify Task 2 (Step 2.2) Creation
    # Step 2.2 should be next
    step_2_2 = WorkflowStep.objects.filter(sequence_id='2.2').first()
    task_2 = Task.objects.filter(project=project, workflow_step=step_2_2).first()
    
    if task_2:
        print(f"SUCCESS: Task 2 auto-created: {task_2}")
        print(f"Task 2 Status: {task_2.status}")
        print(f"Task 2 assigned to: {task_2.assigned_to}") # Should be None/Pending usually
    else:
        print("FAILURE: Task 2 was not created.")
        # Debug
        print(f"Total tasks for project: {Task.objects.filter(project=project).count()}")

if __name__ == "__main__":
    test_dms_flow()
