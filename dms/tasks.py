from celery import shared_task
from .models import Document, Task, Notification, UserDepartmentRole
from django.utils import timezone
import time

@shared_task
def process_document_ai(document_id):
    """
    Simulates AI processing: OCR extraction and Summarization.
    """
    try:
        doc = Document.objects.get(id=document_id)
        doc.embedding_status = 'PENDING'
        doc.save()
        
        # Simulate Processing Delay
        time.sleep(2)
        
        # Placeholder for actual AI Logic (e.g. Call OpenAI, Tesseract)
        # For now, just dummy text
        doc.extracted_text = f"Extracted text content from {doc.file.name}..."
        doc.ai_summary = f"Auto-generated summary for {doc.document_type}."
        doc.embedding_status = 'PROCESSED'
        doc.save()
        
        return f"Document {document_id} processed successfully."
        
    except Document.DoesNotExist:
        return f"Document {document_id} not found."
    except Exception as e:
        if 'doc' in locals():
            doc.embedding_status = 'FAILED'
            doc.save()
        return f"Error processing document {document_id}: {str(e)}"

@shared_task
def check_sla_breaches():
    """
    Periodic task to check for overdue tasks and notify relevant users.
    """
    now = timezone.now()
    overdue_tasks = Task.objects.filter(
        status__in=['PENDING', 'ASSIGNED', 'IN_PROGRESS'],
        due_date__lt=now
    ).exclude(notifications__notification_type='OVERDUE', notifications__is_read=False)
    
    count = 0
    for task in overdue_tasks:
        # 1. Notify Assignee
        if task.assigned_to:
            Notification.objects.create(
                recipient=task.assigned_to,
                title="Task Overdue",
                message=f"Task {task.workflow_step.sequence_id} is overdue.",
                notification_type='OVERDUE',
                related_task=task,
                related_project=task.project
            )
            
        # 2. Notify HOD of the actor department
        # We need to find the HOD of task.workflow_step.actor_department
        hods = UserDepartmentRole.objects.filter(
            department=task.workflow_step.actor_department,
            role='HOD'
        )
        for hod in hods:
            Notification.objects.create(
                recipient=hod.user,
                title="Department Task Overdue",
                message=f"Task {task.workflow_step.sequence_id} in your department is overdue.",
                notification_type='OVERDUE',
                related_task=task,
                related_project=task.project
            )
            
        count += 1
        
    return f"Checked SLA. Generated notifications for {count} tasks."

@shared_task
def check_unassigned_tasks():
    """
    Notify HODs about tasks pending assignment for more than 24 hours (or just pending).
    Let's say pending for > 24 hours.
    """
    now = timezone.now()
    # threshold = now - timezone.timedelta(hours=24) # Optional: only old unassigned
    
    pending_tasks = Task.objects.filter(
        status='PENDING',
        assigned_to__isnull=True
    ).exclude(notifications__notification_type='UNASSIGNED', notifications__created_at__gte=now - timezone.timedelta(days=1))
    # Avoid spamming: don't notify if we notified for this type in last 24h? 
    # Valid filter: exclude(notifications__notification_type='UNASSIGNED', notifications__created_at__gte=today)
    
    count = 0
    for task in pending_tasks:
        hods = UserDepartmentRole.objects.filter(
            department=task.workflow_step.actor_department,
            role='HOD'
        )
        for hod in hods:
             Notification.objects.create(
                recipient=hod.user,
                title="Unassigned Task",
                message=f"Task {task.workflow_step.sequence_id} is waiting for assignment.",
                notification_type='UNASSIGNED',
                related_task=task,
                related_project=task.project
            )
        count += 1
    return f"Checked unassigned tasks. Notified {count} tasks."

@shared_task
def check_project_schedule_status():
    """
    Checks project Schedule Performance Index (SPI) or Variance.
    Simplified: Compare P6 Baseline Finish vs Actual/Current Finish for critical path or major milestones.
    Or simply: Check all linked P6 activities that should have finished by today.
    """
    # Simple Logic: 
    # Find all active projects.
    # For each, find P6 Activities linked to tasks.
    # Calculate how many are behind schedule.
    # If > 10% behind, notify Project Owner.
    
    from projects.models import Project
    from planning.models import P6Activity
    
    active_projects = Project.objects.filter(status='ongoing')
    now = timezone.now()
    
    for project in active_projects:
        # Get all linked P6 activities for this project
        # Assuming P6Activity links to Task links to Project
        activities = P6Activity.objects.filter(dms_task__project=project)
        
        if not activities.exists():
            continue
            
        total_active_acts = activities.filter(early_finish__lt=now).count()
        if total_active_acts == 0:
            continue
            
        # Behind: Early Finish < Now AND Status != Completed
        delayed_acts = activities.filter(early_finish__lt=now).exclude(status='Completed').count()
        
        delay_ratio = delayed_acts / total_active_acts
        
        status_msg = "On Track"
        if delay_ratio > 0.1: # 10% delayed
            status_msg = "Behind Schedule"
        elif delay_ratio < 0:
            status_msg = "Ahead of Schedule" # Hard to calculate ahead without baseline comparison logic
            
        if status_msg == "Behind Schedule":
            # Notify Owner
            if project.owner_user:
                # Check if we already notified recently to avoid spam
                recent = Notification.objects.filter(
                    recipient=project.owner_user,
                    notification_type='PROJECT_STATUS',
                    related_project=project,
                    created_at__gte=now - timezone.timedelta(days=7) # Weekly reminder
                ).exists()
                
                if not recent:
                    Notification.objects.create(
                        recipient=project.owner_user,
                        title=f"Project {project.code} Behind Schedule",
                        message=f"{delayed_acts} out of {total_active_acts} activities are delayed.",
                        notification_type='PROJECT_STATUS',
                        related_project=project
                    )
    
    return "Checked project schedules."
