from django.urls import path
from .views import LoginAPIView
from .views import (
    SupplierViewSet, DMApprovalViewSet, RawMaterialViewSet,
    InventoryViewSet, ProcurementOrderViewSet, QCResultViewSet,
    MixDesignViewSet, CostElementViewSet, ApprovalWorkflowViewSet
)


# For class-based ViewSets, we need to bind HTTP methods manually
supplier_list = SupplierViewSet.as_view({"get": "list", "post": "create"})
supplier_detail = SupplierViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"})

dmapproval_list = DMApprovalViewSet.as_view({"get": "list", "post": "create"})
dmapproval_detail = DMApprovalViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"})

rawmaterial_list = RawMaterialViewSet.as_view({"get": "list", "post": "create"})
rawmaterial_detail = RawMaterialViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"})

inventory_list = InventoryViewSet.as_view({"get": "list", "post": "create"})
inventory_detail = InventoryViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"})

procurementorder_list = ProcurementOrderViewSet.as_view({"get": "list", "post": "create"})
procurementorder_detail = ProcurementOrderViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"})

qcresult_list = QCResultViewSet.as_view({"get": "list", "post": "create"})
qcresult_detail = QCResultViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"})

mixdesign_list = MixDesignViewSet.as_view({"get": "list", "post": "create"})
mixdesign_detail = MixDesignViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"})

costelement_list = CostElementViewSet.as_view({"get": "list", "post": "create"})
costelement_detail = CostElementViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"})

approvalworkflow_list = ApprovalWorkflowViewSet.as_view({"get": "list", "post": "create"})
approvalworkflow_detail = ApprovalWorkflowViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"})

urlpatterns = [
    path('login/', LoginAPIView.as_view(), name='login'),
    path("suppliers/", supplier_list, name="supplier-list"),
    path("suppliers/<int:pk>/", supplier_detail, name="supplier-detail"),

    # DM Approvals
    path("dm-approvals/", dmapproval_list, name="dmapproval-list"),
    path("dm-approvals/<int:pk>/", dmapproval_detail, name="dmapproval-detail"),

    # Raw Materials
    path("raw-materials/", rawmaterial_list, name="rawmaterial-list"),
    path("raw-materials/<int:pk>/", rawmaterial_detail, name="rawmaterial-detail"),

    # Inventory
    path("inventories/", inventory_list, name="inventory-list"),
    path("inventories/<int:pk>/", inventory_detail, name="inventory-detail"),

    # Procurement Orders
    path("procurement-orders/", procurementorder_list, name="procurementorder-list"),
    path("procurement-orders/<int:pk>/", procurementorder_detail, name="procurementorder-detail"),

    # QC Results
    path("qc-results/", qcresult_list, name="qcresult-list"),
    path("qc-results/<int:pk>/", qcresult_detail, name="qcresult-detail"),

    # Mix Designs
    path("mix-designs/", mixdesign_list, name="mixdesign-list"),
    path("mix-designs/<int:pk>/", mixdesign_detail, name="mixdesign-detail"),

    # Cost Elements
    path("cost-elements/", costelement_list, name="costelement-list"),
    path("cost-elements/<int:pk>/", costelement_detail, name="costelement-detail"),

    # Approval Workflows
    path("approval-workflows/", approvalworkflow_list, name="approvalworkflow-list"),
    path("approval-workflows/<int:pk>/", approvalworkflow_detail, name="approvalworkflow-detail"),
]
