from django.contrib import admin
from .models import (
    Supplier, DMApproval, RawMaterial, Inventory,
    ProcurementOrder, QCResult, MixDesign, CostElement, ApprovalWorkflow
)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "contact_person", "email", "phone", "lead_time_days")
    search_fields = ("name", "contact_person", "email")
    list_filter = ("lead_time_days",)


@admin.register(DMApproval)
class DMApprovalAdmin(admin.ModelAdmin):
    list_display = ("approval_number", "expiry_date")
    search_fields = ("approval_number",)
    list_filter = ("expiry_date",)


@admin.register(RawMaterial)
class RawMaterialAdmin(admin.ModelAdmin):
    list_display = ("material_code", "name", "category", "uom", "primary_supplier", "cost_per_unit", "vat_percentage", "reorder_level")
    search_fields = ("material_code", "name", "category")
    list_filter = ("category", "uom", "primary_supplier", "created_at")
    autocomplete_fields = ("primary_supplier", "dm_approval")


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ("material", "stock_quantity", "location", "last_updated")
    search_fields = ("material__name", "location")
    list_filter = ("last_updated",)


@admin.register(ProcurementOrder)
class ProcurementOrderAdmin(admin.ModelAdmin):
    list_display = ("po_number", "supplier", "material", "order_date", "expected_delivery", "quantity", "price", "status")
    search_fields = ("po_number", "supplier__name", "material__name")
    list_filter = ("status", "order_date", "expected_delivery")
    autocomplete_fields = ("supplier", "material")


@admin.register(QCResult)
class QCResultAdmin(admin.ModelAdmin):
    list_display = ("material", "test_date", "test_plan_id", "outcome")
    search_fields = ("material__name", "test_plan_id", "outcome")
    list_filter = ("outcome", "test_date")
    autocomplete_fields = ("material",)


@admin.register(MixDesign)
class MixDesignAdmin(admin.ModelAdmin):
    list_display = ("grade_name", "material", "dosage", "uom")
    search_fields = ("grade_name", "material__name")
    list_filter = ("grade_name",)
    autocomplete_fields = ("material",)


@admin.register(CostElement)
class CostElementAdmin(admin.ModelAdmin):
    list_display = ("material", "element_name", "cost_value")
    search_fields = ("material__name", "element_name")
    list_filter = ("element_name",)
    autocomplete_fields = ("material",)


@admin.register(ApprovalWorkflow)
class ApprovalWorkflowAdmin(admin.ModelAdmin):
    list_display = ("material", "requested_by", "qc_reviewed_by", "final_approved_by", "status", "created_at")
    search_fields = ("material__name", "requested_by", "qc_reviewed_by", "final_approved_by")
    list_filter = ("status", "created_at")
    autocomplete_fields = ("material",)
