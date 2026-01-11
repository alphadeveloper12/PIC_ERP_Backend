from django.db import models
from estimation.models import BOQItem
from dms.models import Department, Task




from projects.models import SubPhase

class PrimaveraSheet(models.Model):
    subphase = models.ForeignKey(SubPhase, on_delete=models.CASCADE, related_name='primavera_sheets')
    name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='primavera_sheets/', null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.subphase.name})"

class P6Activity(models.Model):
    primavera_sheet = models.ForeignKey(PrimaveraSheet, on_delete=models.CASCADE, related_name='activities', null=True) # null=True for migration
    activity_id = models.CharField(max_length=100)
    erc_code = models.CharField(max_length=100, null=True, blank=True)
    activity_name = models.TextField()
    original_duration = models.FloatField(null=True, blank=True)
    early_start = models.DateTimeField(null=True, blank=True)
    early_finish = models.DateTimeField(null=True, blank=True)
    late_start = models.DateTimeField(null=True, blank=True)
    late_finish = models.DateTimeField(null=True, blank=True)
    total_float = models.FloatField(null=True, blank=True)
    budgeted_total_cost = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    budgeted_total_cost = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    owner = models.CharField(max_length=255, null=True, blank=True)
    
    # DMS Integration
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='p6_activities')
    dms_task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True, related_name='linked_p6_activity')
    
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_finish = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, default='Not Started', choices=[
        ('Not Started', 'Not Started'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed')
    ])

    class Meta:
        unique_together = ('primavera_sheet', 'activity_id')

    def __str__(self):
        return f"{self.activity_id} - {self.activity_name}"
    

class MappingResult(models.Model):
    boq = models.ForeignKey(BOQItem, on_delete=models.CASCADE)
    p6 = models.ForeignKey(P6Activity, on_delete=models.CASCADE)
    confidence = models.FloatField()
