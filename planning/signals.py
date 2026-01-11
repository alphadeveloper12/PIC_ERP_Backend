from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from dms.models import Task
from .models import P6Activity

@receiver(post_save, sender=Task)
def sync_p6_dates(sender, instance, created, **kwargs):
    """
    Syncs DMS Task status changes to P6Activity actual dates.
    """
    # Check if this task is linked to a P6 Activity
    # The P6Activity model has 'dms_task' FK related_name='linked_p6_activity'.
    # Since it's a One-to-Many form Task side (one task could be linked to one activity),
    # or actually P6Activity has FK directly.
    # We can access via reverse relation: instance.linked_p6_activity (which is a RelatedManager or single object if OneToOne)
    # P6Activity defines: related_name='linked_p6_activity'. Wait, FK on P6Activity.
    # So Task instance has reference to P6Activity? No, P6Activity has FK to Task.
    # So `instance.linked_p6_activity.all()` gives us the activities linked to this task.
    
    p6_activities = instance.linked_p6_activity.all()
    
    if not p6_activities.exists():
        return
        
    for p6 in p6_activities:
        save_needed = False
        
        # 1. Start Date (IN_PROGRESS or ASSIGNED?)
        # Let's say when it goes to IN_PROGRESS or directly ASSIGNED, we mark Actual Start.
        if instance.status in ['IN_PROGRESS', 'ASSIGNED'] and not p6.actual_start:
            p6.actual_start = timezone.now()
            save_needed = True
            
        # 2. Finish Date (APPROVED)
        if instance.status == 'APPROVED' and not p6.actual_finish:
            p6.actual_finish = instance.completed_at or timezone.now()
            # If not started, assume started same time (or keep null?)
            if not p6.actual_start:
                 p6.actual_start = p6.actual_finish
            save_needed = True
            
        if save_needed:
            p6.save()
            print(f"Synced P6 Activity {p6.activity_id} dates from Task {instance.id}")
