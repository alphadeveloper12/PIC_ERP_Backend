from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Task

# Signals cleaned up. Workflow logic moved to services.WorkflowEngine
# We can keep basic signals if needed, but for now removing the auto-create-next-task 
# which is now explicit in WorkflowEngine.transition_task

@receiver(post_save, sender=Task)
def task_post_save(sender, instance, created, **kwargs):
    # Log or other non-business logic side effects could go here
    pass
