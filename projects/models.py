# projects/models.py
from django.db import models
from core.models import TimeStampedModel, Company


class ProjectState(models.TextChoices):
    PLANNING = "PLANNING", "Planning"
    ESTIMATION = "ESTIMATION", "Estimation"
    DESIGN = "DESIGN", "Design"
    PROCUREMENT = "PROCUREMENT", "Procurement"
    EXECUTION = "EXECUTION", "Execution"
    ON_HOLD = "ON_HOLD", "On hold"
    HALTED = "HALTED", "Halted"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"
    WARRANTY = "WARRANTY", "Warranty / DLP"


class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Short code, e.g. PRJ-0001",
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="projects",
    )
    owner = models.CharField(max_length=255, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=50, choices=[
        ('planned', 'Planned'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed')
    ])
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        indexes = [
            models.Index(fields=["company", "code"]),
        ]
        unique_together = [("company", "name")]


class SubPhase(models.Model):
    name = models.CharField(max_length=100)  # e.g., Planning, Estimation, Development
    project = models.ForeignKey(Project, related_name='subphases', on_delete=models.CASCADE)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.project.name}"

