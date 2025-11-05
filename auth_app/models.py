from django.db import models
from django.core.validators import MinValueValidator


class Supplier(models.Model):
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    lead_time_days = models.PositiveIntegerField(default=0)  # procurement lead time

    def __str__(self):
        return self.name


class DMApproval(models.Model):
    approval_number = models.CharField(max_length=100, unique=True)
    expiry_date = models.DateField()
    document = models.FileField(upload_to="dm_approvals/", blank=True, null=True)

    def __str__(self):
        return f"{self.approval_number} (expires {self.expiry_date})"


class RawMaterial(models.Model):
    material_code = models.CharField(max_length=50, unique=True)  # e.g., RM-CEM-OPC42.5
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100)  # Cement, Aggregate, Admixture, etc.
    uom = models.CharField(max_length=20)  # Controlled list (kg, ton, bag, L, etc.)
    conversion_factor = models.FloatField(default=1.0)  # e.g. Ton → KG
    primary_supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, related_name="materials")
    dm_approval = models.ForeignKey(DMApproval, on_delete=models.SET_NULL, null=True, blank=True)
    
    standards = models.CharField(max_length=255, blank=True, null=True)  # ASTM/BS EN
    qc_test_plan_id = models.CharField(max_length=100)  # link to QC Test Plan
    safety_msds = models.FileField(upload_to="msds/", blank=True, null=True)
    storage_requirements = models.TextField(blank=True, null=True)
    
    cost_per_unit = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    vat_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    co2_factor = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)  # kg CO2 / ton
    
    reorder_level = models.FloatField(default=0.0)
    reorder_quantity = models.FloatField(default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.material_code} - {self.name}"


class Inventory(models.Model):
    material = models.ForeignKey(RawMaterial, on_delete=models.CASCADE)
    stock_quantity = models.FloatField(default=0.0)
    location = models.CharField(max_length=255, blank=True, null=True)  # Bin Card / Silo / Warehouse
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.material.name} - {self.stock_quantity} {self.material.uom}"


class ProcurementOrder(models.Model):
    po_number = models.CharField(max_length=100, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    material = models.ForeignKey(RawMaterial, on_delete=models.CASCADE)
    order_date = models.DateField()
    expected_delivery = models.DateField()
    quantity = models.FloatField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=50, choices=[
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Delivered", "Delivered"),
        ("Cancelled", "Cancelled"),
    ], default="Pending")

    def __str__(self):
        return f"PO-{self.po_number} ({self.material.name})"


class QCResult(models.Model):
    material = models.ForeignKey(RawMaterial, on_delete=models.CASCADE)
    test_date = models.DateField()
    test_plan_id = models.CharField(max_length=100)
    outcome = models.CharField(max_length=100)  # Pass / Fail / Tolerance values
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.material.name} QC-{self.test_plan_id} ({self.outcome})"


class MixDesign(models.Model):
    grade_name = models.CharField(max_length=100)  # e.g. C25/30
    material = models.ForeignKey(RawMaterial, on_delete=models.CASCADE)
    dosage = models.FloatField()  # kg/m3 or L/m3 depending on UoM
    uom = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.grade_name} - {self.material.name} ({self.dosage}{self.uom})"


class CostElement(models.Model):
    material = models.ForeignKey(RawMaterial, on_delete=models.CASCADE)
    element_name = models.CharField(max_length=100)  # Transport, Handling, Customs, etc.
    cost_value = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.material.name} - {self.element_name}: {self.cost_value}"


class ApprovalWorkflow(models.Model):
    material = models.ForeignKey(RawMaterial, on_delete=models.CASCADE)
    requested_by = models.CharField(max_length=255)
    qc_reviewed_by = models.CharField(max_length=255, blank=True, null=True)
    final_approved_by = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=50, choices=[
        ("Requested", "Requested"),
        ("QC Reviewed", "QC Reviewed"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
    ], default="Requested")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.material.name} - {self.status}"
