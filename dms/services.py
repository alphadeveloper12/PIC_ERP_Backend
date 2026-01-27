from django.utils import timezone
from django.db import transaction
from .models import Task, WorkflowStep, Document
from .tasks import process_document_ai

class WorkflowEngine:
    @staticmethod
    def transition_task(task: Task, action: str, user, comments: str = None, assigned_to = None):
        """
        Handles state transitions for a Task.
        action: 'ASSIGN', 'SUBMIT', 'APPROVE', 'REJECT', 'RETURN'
        """
        if action == 'RETURN':
            # HOD returns task to Project Owner (misassigned)
            task.status = 'RETURNED'
            task.assigned_to = None # Clear assignee
            
        elif action == 'ASSIGN':
            if not assigned_to:
                raise ValueError("assigned_to is required for ASSIGN action")
            task.assigned_to = assigned_to
            task.status = 'ASSIGNED'
            
        elif action == 'SUBMIT':
            task.status = 'SUBMITTED'
            
        elif action == 'START':
             # Custom action to mark as in progress
             task.status = 'IN_PROGRESS'
             WorkflowEngine._sync_p6_activity(task, status='In Progress')
        elif action == 'APPROVE':
            # Document Check: If step requires a document, ensure it exists
            if task.workflow_step and task.workflow_step.required_document_type:
                exists = task.documents.filter(document_type=task.workflow_step.required_document_type).exists()
                if not exists:
                    raise ValueError(f"Missing required document: {task.workflow_step.required_document_type}")

            task.status = 'APPROVED'
            task.completed_at = timezone.now()
            WorkflowEngine._sync_p6_activity(task, status='Completed')

            # Generate next task
            WorkflowEngine.create_next_task(task)
            
        elif action == 'REJECT':
            # Instead of just REJECTED, send it back to the assignee for fixing
            # If it has a parent task, re-open the parent task as well
            if task.parent_task:
                parent = task.parent_task
                parent.status = 'IN_PROGRESS'
                parent.comments = f"REJECTED BY REVIEWER: {comments}" if comments else "REJECTED BY REVIEWER"
                parent.save()
                
                # Mark current review task as REJECTED to end its lifecycle
                task.status = 'REJECTED'
            else:
                # If no parent, just move back to ASSIGNED for the same person
                task.status = 'ASSIGNED' 
            
        if comments:
            task.comments = comments
            
        task.save()
        
        # --- Notification Generation ---
        from .models import Notification
        
        task_title = WorkflowEngine._get_task_title(task)

        if action == 'ASSIGN' and assigned_to:
            Notification.objects.create(
                recipient=assigned_to,
                title="New Task Assigned",
                message=f"You have been assigned: {task_title}",
                notification_type='UNASSIGNED', # or generic
                related_task=task,
                related_project=task.project
            )
            
        elif action == 'REJECT':
             # Notify the person it was rejected TO (the assignee)
             if task.assigned_to:
                Notification.objects.create(
                    recipient=task.assigned_to,
                    title="Task Rejected",
                    message=f"Task rejected ({task_title}): {comments}",
                    notification_type='GENERAL',
                    related_task=task,
                    related_project=task.project
                )
                
        elif action == 'SUBMIT':
            # Notify HOD(s) of the Department responsible for this step
            from .models import UserDepartmentRole
            
            # Find HODs for this project & department
            if task.workflow_step and task.workflow_step.actor_department:
                hods = UserDepartmentRole.objects.filter(
                    project=task.project, 
                    department=task.workflow_step.actor_department,
                    role='HOD'
                )
                submitter = "A member"
                if task.assigned_to:
                    submitter = task.assigned_to.get_full_name() or task.assigned_to.username

                for role in hods:
                     Notification.objects.create(
                        recipient=role.user,
                        title="Task Submitted for Approval",
                        message=f"{submitter} submitted: {task_title}",
                        notification_type='GENERAL',
                        related_task=task,
                        related_project=task.project
                    )
            
            # Fallback: Notify Project Owner if no HOD found (or always?)
            elif task.project.owner_user:
                 Notification.objects.create(
                    recipient=task.project.owner_user,
                    title="Task Submitted (No HOD Found)",
                    message=f"Task submitted: {task_title}",
                    notification_type='GENERAL',
                    related_task=task,
                    related_project=task.project
                )

        elif action == 'APPROVE':
            # Notify Project Owner
            if task.project.owner_user:
                  Notification.objects.create(
                    recipient=task.project.owner_user,
                    title="Task Approved",
                    message=f"Task approved: {task_title}",
                    notification_type='GENERAL',
                    related_task=task,
                    related_project=task.project
                )
                
        elif action == 'RETURN':
             # Notify Project Owner
             if task.project.owner_user:
                Notification.objects.create(
                    recipient=task.project.owner_user,
                    title="Task Returned by HOD",
                    message=f"HOD returned task ({task_title}): {comments or 'Incorrect Department'}",
                    notification_type='UNASSIGNED',
                    related_task=task,
                    related_project=task.project
                )

        if action == 'ASSIGN':
             # Also sync P6 on assign if it wasn't started
             WorkflowEngine._sync_p6_activity(task, status='In Progress')
             
        return task

    @staticmethod
    def _sync_p6_activity(task: Task, status: str):
        """
        Helper to sync P6Activity status and dates.
        Traverses back through parent tasks to find the linked P6 Activity.
        """
        try:
            # Avoid circular import
            from django.apps import apps
            P6Activity = apps.get_model('planning', 'P6Activity')
            
            # Find activities linked to this task OR any parent task
            curr = task
            visited = set()
            while curr and curr.id not in visited:
                visited.add(curr.id)
                p6_activities = P6Activity.objects.filter(dms_task=curr)
                for p6_act in p6_activities:
                    p6_act.status = status
                    now = timezone.now()
                    
                    if status == 'In Progress':
                        now = timezone.now()
                        if not p6_act.early_start:
                            p6_act.early_start = now
                        if not p6_act.late_start:
                            p6_act.late_start = now
                        p6_act.actual_start = now
                        
                    elif status == 'Completed':
                        now = timezone.now()
                        if not p6_act.early_start:
                            p6_act.early_start = now
                        p6_act.early_finish = now
                        if not p6_act.late_start:
                            p6_act.late_start = now
                        p6_act.late_finish = now
                        
                        if not p6_act.actual_start:
                            p6_act.actual_start = now
                        p6_act.actual_finish = now
                        
                    p6_act.save()
                
                # Move to parent
                curr = curr.parent_task
        except Exception as e:
            print(f"P6 Sync Error: {e}")

    @staticmethod
    def _get_task_title(task: Task) -> str:
        """
        Returns the P6 Activity Name if available, otherwise the workflow action description.
        """
        try:
            from django.apps import apps
            P6Activity = apps.get_model('planning', 'P6Activity')
            
            # Check current task
            p6_act = P6Activity.objects.filter(dms_task=task).first()
            if p6_act:
                return p6_act.activity_name
            
            # Check parents
            curr = task.parent_task
            visited = {task.id}
            while curr and curr.id not in visited:
                visited.add(curr.id)
                p6_act = P6Activity.objects.filter(dms_task=curr).first()
                if p6_act:
                    return p6_act.activity_name
                curr = curr.parent_task
                
        except Exception:
            pass
            
        return task.workflow_step.action_description if task.workflow_step else "Custom Task"

    @staticmethod
    def create_next_task(current_task: Task):
        """
        Determines and creates the next task in the workflow.
        """
        current_step = current_task.workflow_step
        project = current_task.project
        
        next_step = WorkflowEngine.get_next_step(current_step)
        
        if next_step:
            # Check idempotency
            existing = Task.objects.filter(project=project, workflow_step=next_step).first()
            if not existing:
                new_task = Task.objects.create(
                    project=project,
                    workflow_step=next_step,
                    status='PENDING',
                    parent_task=current_task
                )
                
                # Dynamic Due Date Logic:
                # 1. Try to inherit from linked P6 Activity (Early Finish)
                from django.apps import apps
                P6Activity = apps.get_model('planning', 'P6Activity')
                # Find P6 activity linked in the chain
                curr = current_task
                p6_finish = None
                visited = set()
                while curr and curr.id not in visited:
                    visited.add(curr.id)
                    act = P6Activity.objects.filter(dms_task=curr).first()
                    if act and act.early_finish:
                        p6_finish = act.early_finish
                        break
                    curr = curr.parent_task
                
                if p6_finish:
                    new_task.due_date = p6_finish
                elif next_step.sla_hours:
                    # 2. Fallback to SLA
                    new_task.due_date = timezone.now() + timezone.timedelta(hours=next_step.sla_hours)
                
                new_task.save()
                return new_task
            else:
                if not existing.parent_task:
                    existing.parent_task = current_task
                    existing.save()
                return existing
        return None

    @staticmethod
    def get_next_step(current_step: WorkflowStep):
        """
        Finds the next step within the same Workflow Template / Phase.
        """
        # 1. Custom branching from the model
        next_custom = current_step.next_possible_steps.first()
        if next_custom:
            return next_custom
            
        # 2. Next in Phase
        next_in_phase = WorkflowStep.objects.filter(
            phase=current_step.phase,
            ordering__gt=current_step.ordering
        ).order_by('ordering').first()
        
        if next_in_phase:
            return next_in_phase
            
        # 3. Next Phase within the same TEMPLATE
        current_template = current_step.phase.template
        if current_template:
            next_phase = WorkflowPhase.objects.filter(
                template=current_template,
                sequence__gt=current_step.phase.sequence
            ).order_by('sequence').first()
            
            if next_phase:
                return WorkflowStep.objects.filter(phase=next_phase).order_by('ordering').first()
        else:
            # Fallback for legacy global phases without template
            next_phase_seq = current_step.phase.sequence + 1
            next_step_new_phase = WorkflowStep.objects.filter(
                phase__sequence=next_phase_seq,
                phase__template__isnull=True # Stay global if we started global
            ).order_by('ordering').first()
            return next_step_new_phase
            
        return None

class DocumentService:
    @staticmethod
    def upload_document(task: Task, file, user, document_type: str):
        doc = Document.objects.create(
            task=task,
            project=task.project,
            uploaded_by=user,
            file=file,
            document_type=document_type,
            version=1 # Logic for versioning could go here
        )
        
        # Trigger Async AI Processing
        transaction.on_commit(lambda: process_document_ai.delay(doc.id))
        
        return doc
