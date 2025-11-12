from django.db import models
from projects.models import SubPhase
# Create your models here.


class Planning(models.Model):
    subphase = models.ForeignKey(SubPhase, related_name='plannings', on_delete=models.CASCADE)


class Schedule(models.Model):
    """
    Represents a complete imported Primavera schedule under a Planning phase.
    """
    planning = models.ForeignKey(Planning, related_name="schedules", on_delete=models.CASCADE)
    external_id = models.CharField(max_length=50, unique=True, help_text="Primavera Project ID")
    name = models.CharField(max_length=255)
    imported_on = models.DateTimeField(auto_now_add=True)
    start_date = models.DateField(null=True, blank=True)
    finish_date = models.DateField(null=True, blank=True)
    calendar_name = models.CharField(max_length=255, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.planning.subphase.project.code})"


class WorkBreakdownItem(models.Model):
    """
    Represents a WBS (Work Breakdown Structure) element imported from Primavera.
    """
    schedule = models.ForeignKey(Schedule, related_name="wbs_items", on_delete=models.CASCADE)
    external_id = models.CharField(max_length=50, db_index=True)
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=100, blank=True, null=True)
    level = models.IntegerField(default=0)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    weight = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.schedule.name})"


class Task(models.Model):
    """
    Represents an activity/task under a WBS element.
    """
    wbs_item = models.ForeignKey(WorkBreakdownItem, related_name="tasks", on_delete=models.CASCADE)
    external_id = models.CharField(max_length=50, db_index=True)
    name = models.CharField(max_length=255)
    start_date = models.DateField(null=True, blank=True)
    finish_date = models.DateField(null=True, blank=True)
    duration = models.FloatField(null=True, blank=True)
    percent_complete = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    critical_flag = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.wbs_item.name})"


class TaskDependency(models.Model):
    """
    Defines predecessor-successor relationships among tasks.
    """
    predecessor = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="successors_links")
    successor = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="predecessors_links")
    relation_type = models.CharField(max_length=10, choices=[
        ('FS', 'Finish to Start'),
        ('SS', 'Start to Start'),
        ('FF', 'Finish to Finish'),
        ('SF', 'Start to Finish')
    ], default='FS')
    lag = models.FloatField(default=0)

    class Meta:
        unique_together = ('predecessor', 'successor', 'relation_type')


class Resource(models.Model):
    """
    Represents a human or material resource.
    """
    schedule = models.ForeignKey(Schedule, related_name="resources", on_delete=models.CASCADE)
    external_id = models.CharField(max_length=50, db_index=True)
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    rate = models.FloatField(null=True, blank=True)
    currency = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.schedule.name})"


class Assignment(models.Model):
    """
    Links tasks to resources.
    """
    task = models.ForeignKey(Task, related_name="assignments", on_delete=models.CASCADE)
    resource = models.ForeignKey(Resource, related_name="assignments", on_delete=models.CASCADE)
    planned_units = models.FloatField(null=True, blank=True)
    actual_units = models.FloatField(null=True, blank=True)
    cost = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = ('task', 'resource')


class XerImportJob(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ]

    planning = models.ForeignKey('Planning', on_delete=models.CASCADE)
    file = models.FileField(upload_to='xer_imports/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    message = models.TextField(blank=True, null=True)
    summary = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"XER Import Job #{self.id} ({self.status})"
    