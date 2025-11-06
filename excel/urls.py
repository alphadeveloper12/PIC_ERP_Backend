from django.urls import path
from .views import *

urlpatterns = [
    path('upload-bill/', UploadBillView.as_view()),
    path('config/', ConfigView.as_view()),
    path('bill-items/', BillItemListView.as_view()),
    path('bill-grouped/', BillGroupedView.as_view()),
    path('bill-items/<int:pk>/', BillItemUpdateView.as_view()),
    path('bill-items/create/', BillItemCreateView.as_view()),
    path('bill-items/<int:pk>/soft-delete/', BillItemSoftDeleteView.as_view()),
    path('bill-items/<int:pk>/restore/', BillItemRestoreView.as_view()),
    path('bill-items/<int:pk>/hard-delete/', BillItemHardDeleteView.as_view()),
    path('reorder/', ReorderView.as_view()),
    path('export/excel/', ExportExcelView.as_view()),
    path('export/pdf/', ExportPDFView.as_view()),
    path('projects/', ProjectView.as_view()),   # New route to manage projects
    path('projects/<int:project_id>/revisions/', RevisionView.as_view()),  # Route to upload revisions for a project
    path('estimation/save/', EstimationSaveView.as_view()),
    path('estimation/<int:item_id>/', EstimationUpdateView.as_view()),
]
