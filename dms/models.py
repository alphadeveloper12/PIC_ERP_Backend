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
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='team_roles', null=True) # Null for migration, strictly required later
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='department_roles')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='members')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='OFFICER')

    class Meta:
        unique_together = ('user', 'department', 'project')

    def __str__(self):
        return f"{self.user.username} - {self.department.code} ({self.role})"

class AccessPolicy(models.Model):
    """
    Defines permissions for each role within a department, scoped to a project.
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='access_policies', null=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='access_policies')
    role = models.CharField(max_length=20, choices=UserDepartmentRole.ROLE_CHOICES)
    permissions = models.JSONField(
        default=list, 
        help_text="List of permission codes (e.g. ['view_procurement', 'approve_tasks'])"
    )

    class Meta:
        unique_together = ('project', 'department', 'role')

    def __str__(self):
        proj_code = self.project.code if self.project else "Global"
        return f"[{proj_code}] {self.department.code} - {self.role} Policy"

class WorkflowTemplate(models.Model):
    """
    Defines a specific process flow (e.g., Procurement Standard, Engineering Design).
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class WorkflowPhase(models.Model):
    """
    Groups steps into phases like 'Tendering', 'Mobilization'.
    """
    template = models.ForeignKey(WorkflowTemplate, on_delete=models.CASCADE, related_name='phases', null=True, blank=True)
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
    
    # Advanced Workflow
    sla_hours = models.PositiveIntegerField(default=24, help_text="Expected time to complete this step in hours")
    # Simple branching support: define which steps can follow this one. 
    # If empty, default logic (next in sequence) applies.
    next_possible_steps = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='previous_steps')

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
    workflow_step = models.ForeignKey(WorkflowStep, on_delete=models.SET_NULL, null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # HOD assigns to a specific user
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='dms_assignments')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    
    comments = models.TextField(blank=True, null=True)
    
    # Workflow Traceability
    parent_task = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='next_tasks')

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
    
    # AI Enhancements
    ai_summary = models.TextField(blank=True, null=True)
    extracted_text = models.TextField(blank=True, null=True)
    
    class EmbeddingStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PROCESSED = 'PROCESSED', 'Processed'
        FAILED = 'FAILED', 'Failed'
        
    embedding_status = models.CharField(
        max_length=20, 
        choices=EmbeddingStatus.choices, 
        default=EmbeddingStatus.PENDING
    )

    def __str__(self):
        return f"{self.project.code} - {self.document_type} (v{self.version})"
class DepartmentWorkflowMapping(models.Model):
    """
    Maps a department to a specific workflow template.
    Allows for default templates per department.
    """
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='workflow_mappings')
    template = models.ForeignKey(WorkflowTemplate, on_delete=models.CASCADE)
    activity_type_prefix = models.CharField(max_length=50, blank=True, null=True, help_text="Optional: Only apply if activity ID starts with this.")
    priority = models.IntegerField(default=0, help_text="Higher priority takes precedence.")

    class Meta:
        ordering = ['-priority']
        unique_together = ('department', 'activity_type_prefix')

    def __str__(self):
        return f"{self.department.code} -> {self.template.name}"
