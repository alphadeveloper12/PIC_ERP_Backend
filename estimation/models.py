# estimation/models.py
from django.db import models
from core.models import TimeStampedModel, Company, Profile, Currency
from projects.models import Project, SubPhase
from django.core.exceptions import ValidationError
import hashlib
import os
from django.utils import timezone


def boq_file_upload_to(instance, filename):
    project_name = instance.estimation.subphase.project.name
    return os.path.join(project_name, 'BOQ', filename)


class EstimationStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    UNDER_REVIEW = "UNDER_REVIEW", "Under review"
    APPROVED = "APPROVED", "Approved"
    LOCKED = "LOCKED", "Locked"
    ARCHIVED = "ARCHIVED", "Archived"


class Estimation(models.Model):
    subphase = models.ForeignKey(SubPhase, related_name='estimations', on_delete=models.CASCADE)
    total_estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    notes = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=EstimationStatus.choices,
        default=EstimationStatus.DRAFT,
        db_index=True,
    )
    prepared_by = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prepared_estimations",
    )
    approved_by = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_estimations",
    )
    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Estimation for {self.subphase.name} - {self.total_estimated_cost}"


class BOQ(TimeStampedModel):
    name = models.CharField(max_length=255)
    estimation = models.ForeignKey(Estimation, related_name='boqs', on_delete=models.CASCADE)
    file_path = models.FileField(upload_to=boq_file_upload_to, blank=True, null=True)
    file_hash = models.CharField(max_length=64, unique=True, blank=True, null=True)  # SHA256 hash

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.file_path:
            self.file_hash = self.calculate_file_hash(self.file_path)
            super().save(update_fields=['file_hash'])

    def calculate_file_hash(self, file):
        """
        Calculate the SHA256 hash of the file content.
        """
        hash_sha256 = hashlib.sha256()
        with open(file.path, 'rb') as f:
            # Read and update the hash string value in blocks of 4K
            for byte_block in iter(lambda: f.read(4096), b""):
                hash_sha256.update(byte_block)
        return hash_sha256.hexdigest()


class Section(models.Model):
    name = models.CharField(max_length=200)  # e.g., "SECTION B - SITE WORK"
    boq = models.ForeignKey(BOQ, related_name='sections', on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Subsection(models.Model):
    name = models.CharField(max_length=200)  # e.g., "B4 - SITE PREPARATION"
    section = models.ForeignKey(Section, related_name='subsections', on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class BOQItem(models.Model):
    description = models.CharField(max_length=255)  # e.g., "Soil treatment"
    unit = models.CharField(max_length=50)  # e.g., "m2"
    quantity = models.DecimalField(max_digits=10, decimal_places=2)  # Quantity of the item
    rate = models.DecimalField(max_digits=10, decimal_places=2)  # Rate per unit
    amount = models.DecimalField(max_digits=12, decimal_places=2)  # Total cost for this item
    subsection = models.ForeignKey(Subsection, related_name='items', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.description} ({self.unit})"

    def clean(self):
        if self.quantity == '':
            self.quantity = None
        if self.rate == '':
            self.rate = None
        if self.amount == '':
            self.amount = None

        # Continue with the validation
        if self.quantity is None or self.rate is None or self.amount is None:
            raise ValidationError('Quantity, rate, and amount must not be empty.')

        if self.quantity < 0 or self.rate < 0 or self.amount < 0:
            raise ValidationError('Quantity, rate, and amount must be non-negative values.')


class BOQRevision(models.Model):
    boq = models.ForeignKey(BOQ, related_name='revisions', on_delete=models.CASCADE)
    section = models.ForeignKey(Section, null=True, blank=True, on_delete=models.SET_NULL)
    subsection = models.ForeignKey(Subsection, null=True, blank=True, on_delete=models.SET_NULL)
    boq_item = models.ForeignKey(BOQItem, null=True, blank=True, on_delete=models.SET_NULL)
    old_value = models.TextField()
    new_value = models.TextField()
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Revision for BOQ {self.boq.name} at {self.updated_at}"

    class Meta:
        ordering = ['-updated_at']


class CostItemCategory(models.TextChoices):
    MATERIAL = "MATERIAL", "Material"
    LABOUR = "LABOUR", "Labour"
    PLANT = "PLANT", "Plant / Equipment"
    SUBCONTRACT = "SUBCONTRACT", "Subcontract"
    OTHER = "OTHER", "Other"


class CostItem(TimeStampedModel):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="cost_items",
    )
    code = models.CharField(max_length=50)
    description = models.TextField()
    category = models.CharField(
        max_length=20,
        choices=CostItemCategory.choices,
        db_index=True,
    )
    unit = models.CharField(max_length=50)
    default_rate = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("company", "code")]
        indexes = [
            models.Index(fields=["company", "category"]),
        ]

    def __str__(self):
        return f"{self.code} - {self.description[:40]}"
