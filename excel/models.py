from django.db import models
from django.utils import timezone

class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Revision(models.Model):
    project = models.ForeignKey(Project, related_name="revisions", on_delete=models.CASCADE)
    version = models.IntegerField()
    file = models.FileField(upload_to="revisions/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Revision {self.version} for {self.project.name}"


class AppConfigKV(models.Model):
    # simple persisted add-ons
    tax_rate = models.FloatField(default=0.0)        # e.g., 0.18 for 18%
    overhead_rate = models.FloatField(default=0.0)   # e.g., 0.05 for 5%
    brand_title = models.CharField(max_length=200, default="Bill of Quantities")
    brand_subtitle = models.CharField(max_length=300, blank=True, default="")
    logo_url = models.CharField(max_length=500, blank=True, default="")  # public URL/file path

    def __str__(self):
        return "BOQ App Configuration"


class Material(models.Model):
    bill_item = models.ForeignKey('BillItem', related_name='materials', on_delete=models.CASCADE)
    material_name = models.CharField(max_length=200)
    material_rate = models.FloatField(blank=True, null=True)
    material_quantity = models.FloatField(blank=True, null=True)
    material_wastage = models.FloatField(blank=True, null=True, default=1.0)
    material_amount = models.FloatField(blank=True, null=True, default=0.0)

    def save(self, *args, **kwargs):
        # Automatically calculate material amount
        self.material_amount = (self.material_rate or 0) * (self.material_quantity or 0) * (self.material_wastage or 1)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.material_name} for {self.bill_item}"


class BillItem(models.Model):
    project = models.ForeignKey('Project', related_name='bill_items', on_delete=models.CASCADE)
    section = models.CharField(max_length=120, blank=True, null=True)
    item_no = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    unit = models.CharField(max_length=50, blank=True, null=True)
    quantity = models.FloatField(blank=True, null=True)
    rate = models.FloatField(blank=True, null=True)
    amount = models.FloatField(blank=True, null=True)
    section_factor = models.FloatField(default=0.0)

    # Estimation fields
    material_rate = models.FloatField(blank=True, null=True)
    material_wastage = models.FloatField(blank=True, null=True)
    material_u_rate = models.FloatField(blank=True, null=True)
    material_amount = models.FloatField(blank=True, null=True)

    plant_rate = models.FloatField(blank=True, null=True)
    plant_amount = models.FloatField(blank=True, null=True)

    labour_hours = models.FloatField(blank=True, null=True)
    labour_amount = models.FloatField(blank=True, null=True)

    subcontract_rate = models.FloatField(blank=True, null=True)
    subcontract_amount = models.FloatField(blank=True, null=True)

    others_1_qty = models.FloatField(blank=True, null=True)
    others_1_rate = models.FloatField(blank=True, null=True)
    others_1_amount = models.FloatField(blank=True, null=True)

    others_2_qty = models.FloatField(blank=True, null=True)
    others_2_rate = models.FloatField(blank=True, null=True)
    others_2_amount = models.FloatField(blank=True, null=True)

    dry_cost = models.FloatField(blank=True, null=True)
    unit_rate = models.FloatField(blank=True, null=True)
    prelimin = models.FloatField(blank=True, null=True)

    boq_amount = models.FloatField(blank=True, null=True)

    actual_qty = models.FloatField(blank=True, null=True)
    actual_amount = models.FloatField(blank=True, null=True)

    sort_order = models.IntegerField(default=0)

    # Soft delete
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_reason = models.CharField(max_length=200, blank=True, default="")

    # Factor field (percentage) added for section-wise calculation
    factor = models.FloatField(default=0.0)

    def save(self, *args, **kwargs):
        # Check if we should recalculate amounts
        force_calculation = kwargs.pop('force_calculation', False)
        is_new = self.pk is None
        
        # First save to ensure we have a primary key
        super().save(*args, **kwargs)
        
        # Only perform calculations after initial save (when materials exist)
        # or when explicitly requested
        if force_calculation and not is_new:
            # Calculate material amount from related materials
            material_sum = sum(
                material.material_amount or 0.0 
                for material in self.materials.all()
            )
            
            # Apply factor to material amount
            self.material_amount = material_sum * (1 + (self.factor or 0.0) / 100)
            self.plant_amount = (self.plant_rate or 0) * (self.quantity or 0)
            self.labour_amount = (self.labour_hours or 0) * (self.rate or 0)
            self.subcontract_amount = (self.subcontract_rate or 0) * (self.quantity or 0)
            self.others_1_amount = (self.others_1_qty or 0) * (self.others_1_rate or 0)
            self.others_2_amount = (self.others_2_qty or 0) * (self.others_2_rate or 0)
            self.boq_amount = (
                (self.material_amount or 0) + 
                (self.plant_amount or 0) + 
                (self.labour_amount or 0) + 
                (self.subcontract_amount or 0) + 
                (self.others_1_amount or 0) + 
                (self.others_2_amount or 0)
            )
            
            # Save again with only calculated fields updated
            super().save(update_fields=[
                'material_amount', 'plant_amount', 'labour_amount',
                'subcontract_amount', 'others_1_amount', 'others_2_amount',
                'boq_amount'
            ])

    class Meta:
        ordering = ["section", "sort_order", "id"]

    def __str__(self):
        return f"{self.section or ''} - {self.description or 'Item'}"

    def soft_delete(self, reason=""):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_reason = reason
        self.save()

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_reason = ""
        self.save()