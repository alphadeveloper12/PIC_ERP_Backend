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
    factor = models.FloatField(default=0.0)
    boq = models.ForeignKey(BOQ, related_name='sections', on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Subsection(models.Model):
    name = models.CharField(max_length=200)  # e.g., "B4 - SITE PREPARATION"
    section = models.ForeignKey(Section, related_name='subsections', on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class BOQItem(models.Model):
    subsection = models.ForeignKey('Subsection', related_name='items', on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    unit = models.CharField(max_length=50)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    # Calculated summary fields
    dry_cost = models.FloatField(blank=True, null=True)
    unit_rate = models.FloatField(blank=True, null=True)
    prelimin = models.FloatField(blank=True, null=True)
    boq_amount = models.FloatField(blank=True, null=True)

    # Embedded category cost fields
    labor_hours = models.FloatField(blank=True, null=True, default=0.0)
    labor_amount = models.FloatField(blank=True, null=True, default=0.0)

    plant_rate = models.FloatField(blank=True, null=True, default=0.0)
    plant_amount = models.FloatField(blank=True, null=True, default=0.0)

    subcontract_rate = models.FloatField(blank=True, null=True, default=0.0)
    subcontract_amount = models.FloatField(blank=True, null=True, default=0.0)

    # Other metadata
    sort_order = models.IntegerField(default=0)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_reason = models.CharField(max_length=200, blank=True, default="")
    factor = models.FloatField(default=0.0)

    class Meta:
        ordering = ["subsection", "sort_order", "id"]

    def __str__(self):
        return f"{self.description} ({self.unit})"

    def add_labour(self, hours):
        self.labor_hours = hours
        self.save()

    def add_plant(self, rate):
        self.plant_rate = rate
        self.save()

    def add_subcontract(self, rate):
        self.subcontract_rate = rate
        self.save()

    def save(self, *args, **kwargs):
        """
        Unified save method to calculate all BOQ-related costs directly inside BOQItem.
        """
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # --- Step 1: Compute component costs ---
        # Labour
        if self.labor_hours and self.rate:
            self.labor_amount = (self.plant_rate or 0) * (self.quantity or 0)

        # Plant
        if self.plant_rate:
            self.plant_amount = self.plant_rate * float(self.quantity or 0)

        # Subcontract
        if self.subcontract_rate:
            self.subcontract_amount = self.subcontract_rate * float(self.quantity or 0)

        # --- Step 2: Sum up total materials ---
        material_sum = sum(float(m.amount or 0.0) for m in self.materials.all())

        # Apply factor on materials
        material_sum *= (1 + (self.factor or 0.0) / 100)

        # --- Step 3: Total cost roll-up ---
        total_component_cost = (
                float(self.labor_amount or 0) +
                float(self.plant_amount or 0) +
                float(self.subcontract_amount or 0)
        )

        self.dry_cost = material_sum + float(self.labor_amount or 0) + float(self.plant_amount or 0)
        self.boq_amount = material_sum + total_component_cost

        # --- Step 4: Unit Rate ---
        self.unit_rate = (
            float(self.boq_amount) / float(self.quantity)
            if self.quantity else None
        )

        # Save updated computed fields
        super().save(update_fields=[
            "labor_amount", "plant_amount", "subcontract_amount",
            "boq_amount", "dry_cost", "unit_rate"
        ])


class Material(models.Model):
    boq_item = models.ForeignKey(BOQItem, related_name='materials', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    rate = models.FloatField(blank=True, null=True)
    wastage = models.FloatField(blank=True, null=True)
    u_rate = models.FloatField(blank=True, null=True)
    amount = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.boq_item.description}"

    def save(self, *args, **kwargs):
        """
        Automatically calculate material amount and trigger parent BOQItem recalculation.
        """
        if self.rate is not None and self.u_rate is not None:
            wastage_factor = 1 + (self.wastage or 0) / 100
            self.amount = self.rate * self.u_rate * wastage_factor

        super().save(*args, **kwargs)

        # Trigger roll-up recalculation
        if self.boq_item_id:
            self.boq_item.save(force_calculation=True)


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
