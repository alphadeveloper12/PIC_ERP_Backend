from django.db import models
from django.contrib.auth import get_user_model
from projects.models import Project

User = get_user_model()

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True, help_text="Short code e.g. QS, DEV")
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

class UserDepartmentRole(models.Model):
    ROLE_CHOICES = [
        ('HOD', 'Head of Department'),
        ('OFFICER', ' Officer / Team Member'),
        ('ADMIN', 'Department Admin'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='department_roles')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='members')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='OFFICER')

    class Meta:
        unique_together = ('user', 'department')

    def __str__(self):
        return f"{self.user.username} - {self.department.code} ({self.role})"

class WorkflowPhase(models.Model):
    """
    Groups steps into phases like 'Tendering', 'Mobilization'.
    """
    name = models.CharField(max_length=100)
    sequence = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['sequence']

class WorkflowStep(models.Model):
    """
    Template for a step in the workflow.
    Based on the Excel: Seq | Actor | Action | Document Type | Receiver
    """
    phase = models.ForeignKey(WorkflowPhase, on_delete=models.CASCADE, related_name='steps')
    sequence_id = models.CharField(max_length=20, help_text="e.g. 2.1")
    ordering = models.FloatField(help_text="Numeric value for sorting, e.g. 2.1")
    
    actor_department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='acting_steps')
    action_description = models.TextField()
    required_document_type = models.CharField(max_length=255, blank=True, null=True)
    
    receiver_department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='receiving_steps', null=True, blank=True)
    
    is_start_step = models.BooleanField(default=False, help_text="If True, this step starts a new process.")

    def __str__(self):
        return f"{self.sequence_id}: {self.actor_department.code} -> {self.receiver_department.code if self.receiver_department else 'End'}"

    class Meta:
        ordering = ['ordering']


class Task(models.Model):
    """
    An active instance of a WorkflowStep for a specific Project.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending Assignment'),
        ('ASSIGNED', 'Assigned'),
        ('IN_PROGRESS', 'In Progress'),
        ('SUBMITTED', 'Submitted for Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='dms_tasks')
    workflow_step = models.ForeignKey(WorkflowStep, on_delete=models.CASCADE)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # HOD assigns to a specific user
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='dms_assignments')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    comments = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"[{self.project.code}] {self.workflow_step.sequence_id} - {self.status}"

class Document(models.Model):
    """
    The actual file uploaded for a Task.
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='documents')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='dms_documents') # Redundant but good for quick lookups
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='dms_documents/%Y/%m/%d/')
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    
    document_type = models.CharField(max_length=255, help_text="Matches WorkflowStep.required_document_type")

    def __str__(self):
        return f"{self.project.code} - {self.document_type} (v{self.version})"
