from django.db import models
from projects.models import Project
from django.contrib.auth import get_user_model

User = get_user_model()

class ConstructionContract(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='contracts')
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='contracts/%Y/%m/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Metadata
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    contract_value = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    
    is_processed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} ({self.project.code})"

class ContractClause(models.Model):
    CATEGORY_CHOICES = [
        ('PAYMENT', 'Payment Terms'),
        ('RETENTION', 'Retention'),
        ('ADVANCE', 'Advance Payment'),
        ('INDEMNITY', 'Indemnity'),
        ('TERMINATION', 'Termination'),
        ('DISPUTE', 'Dispute Resolution'),
        ('MILESTONE', 'Milestone'),
        ('GENERAL', 'General'),
    ]

    contract = models.ForeignKey(ConstructionContract, on_delete=models.CASCADE, related_name='clauses')
    department = models.ForeignKey('dms.Department', on_delete=models.SET_NULL, null=True, blank=True, help_text="Department responsible for this clause")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='GENERAL')
    
    original_text = models.TextField()
    interpreted_value = models.JSONField(null=True, blank=True, help_text="Structured data extracted from text")
    
    # Semantic Search
    embedding = models.JSONField(null=True, blank=True, help_text="SBERT vector")
    
    page_number = models.IntegerField(null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category} - {self.contract.title[:20]}"
