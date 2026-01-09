from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Task, WorkflowStep
from django.db.models import Min

@receiver(post_save, sender=Task)
def create_next_task(sender, instance, created, **kwargs):
    """
    When a task is APPROVED, automatically create the next task in the workflow.
    """
    if not created and instance.status == 'APPROVED' and instance.completed_at:
        # Prevent recursion or duplicate creation if saved multiple times? 
        # Ideally check if next task already exists.
        
        current_step = instance.workflow_step
        project = instance.project
        
        # Logic to find the next step
        # 1. Look for next step in same phase with higher ordering
        next_step = WorkflowStep.objects.filter(
            phase=current_step.phase,
            ordering__gt=current_step.ordering
        ).order_by('ordering').first()
        
        # 2. If no next step in phase, look for first step of next phase
        if not next_step:
            next_phase_seq = current_step.phase.sequence + 1
            next_step = WorkflowStep.objects.filter(
                phase__sequence=next_phase_seq
            ).order_by('ordering').first()
            
        if next_step:
            # Check if task already exists for this project and step (idempotency)
            exists = Task.objects.filter(project=project, workflow_step=next_step).exists()
            if not exists:
                Task.objects.create(
                    project=project,
                    workflow_step=next_step,
                    status='PENDING'
                )
                print(f"Auto-created next task: {next_step} for project {project.code}")
