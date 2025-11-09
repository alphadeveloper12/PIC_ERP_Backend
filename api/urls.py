# api/urls.py
from django.urls import path
# from .views import (
#     ProjectView, ProjectDetailView, ProjectPhaseView, ProjectPhaseDetailView,
#     BoqView, BoqDetailView, BoqExcelUploadView
# )
from estimation.views import *
from core.views import CompanyCreateView, CompanyListView, ProfileCreateView, ProfileListView
from projects.views import SubPhaseListView, SubPhaseCreateView, ProjectCreateView, \
    ProjectUpdateView, ProjectDetailView, ProjectListView

urlpatterns = [
    # path("projects/", ProjectView.as_view(), name="project-list-create"),
    # path("projects/<int:project_id>/", ProjectDetailView.as_view(), name="project-detail"),
    #
    # path("projects/<int:project_id>/phases/", ProjectPhaseView.as_view(), name="project-phase-list-create"),
    # path("phases/<int:phase_id>/", ProjectPhaseDetailView.as_view(), name="project-phase-detail"),
    #
    # path("projects/<int:project_id>/boqs/", BoqView.as_view(), name="boq-list-create"),
    # path("boqs/<int:boq_id>/", BoqDetailView.as_view(), name="boq-detail"),
    #
    # path("projects/<int:project_id>/boq-upload/", BoqExcelUploadView.as_view(), name="boq-upload"),

    path('upload/boq/', UploadBOQ.as_view(), name='extract-boq-data'),
    path('boq/', BOQListView.as_view(), name='boq-list'),
    path('boq/<int:pk>/', BOQDetailView.as_view(), name='boq-detail'),
    path('boq/<int:pk>/update/', BOQUpdateView.as_view(), name='boq-update'),
    path('company/create', CompanyCreateView.as_view(), name='boq-update'),
    path('company/list', CompanyListView.as_view(), name='boq-update'),
    path('profile/create', ProfileCreateView.as_view(), name='boq-update'),
    path('profile/list', ProfileListView.as_view(), name='boq-update'),
    path('project/create', ProjectCreateView.as_view(), name='boq-update'),
    path('project/list', ProjectListView.as_view(), name='boq-update'),
    path('project/<int:pk>/update', ProjectUpdateView.as_view(), name='boq-update'),
    path('project/<int:pk>', ProjectDetailView.as_view(), name='boq-update'),
    path('subphase/create', SubPhaseCreateView.as_view(), name='boq-update'),
    path('subphase/list', SubPhaseListView.as_view(), name='boq-update'),
    path('estimation/create', EstimationCreateView.as_view(), name='boq-update'),
    path('estimation/<int:pk>/update', EstimationUpdateView.as_view(), name='boq-update'),
    path('estimation/', EstimationListView.as_view(), name='boq-update'),

    # path('bill-items/', BillItemListView.as_view()),
    path('bill-grouped/', BOQGroupedView.as_view()),
    path('bill-items/<int:pk>/', BOQItemUpdateView.as_view()),
    path('bill-items/create/', BOQItemCreateView.as_view()),
    path('bill-items/<int:pk>/soft-delete/', BOQItemSoftDeleteView.as_view()),
    path('bill-items/<int:pk>/restore/', BOQItemRestoreView.as_view()),
    path('bill-items/<int:pk>/hard-delete/', BOQItemHardDeleteView.as_view()),
    path('reorder/', ReorderView.as_view()),
    path('export/excel/<int:boq_id>', ExportExcelView.as_view()),
    path('export/pdf/<int:boq_id>', ExportPDFView.as_view()),

    # --- MATERIAL ---
    path("materials/", MaterialCreateView.as_view(), name="material-create"),
    path("materials/<int:pk>/", MaterialUpdateView.as_view(), name="material-update"),
    path("materials/by-item/<int:boq_item_id>/", MaterialByBOQItemView.as_view(), name="material-by-item"),

    # --- PLANT ---
    path("plants/", PlantCreateView.as_view(), name="plant-create"),
    path("plants/<int:pk>/", PlantUpdateView.as_view(), name="plant-update"),
    path("plants/by-item/<int:boq_item_id>/", PlantByBOQItemView.as_view(), name="plant-by-item"),

    # --- LABOUR ---
    path("labours/", LabourCreateView.as_view(), name="labour-create"),
    path("labours/<int:pk>/", LabourUpdateView.as_view(), name="labour-update"),
    path("labours/by-item/<int:boq_item_id>/", LabourByBOQItemView.as_view(), name="labour-by-item"),

    # --- SUBCONTRACT ---
    path("subcontracts/", SubcontractCreateView.as_view(), name="subcontract-create"),
    path("subcontracts/<int:pk>/", SubcontractUpdateView.as_view(), name="subcontract-update"),
    path("subcontracts/by-item/<int:boq_item_id>/", SubcontractByBOQItemView.as_view(), name="subcontract-by-item"),

]
