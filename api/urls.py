# api/urls.py
from django.urls import path
# from .views import (
#     ProjectView, ProjectDetailView, ProjectPhaseView, ProjectPhaseDetailView,
#     BoqView, BoqDetailView, BoqExcelUploadView
# )
from estimation.views import UploadBOQ, BOQListView, BOQDetailView, BOQUpdateView, \
    EstimationListView, EstimationCreateView, EstimationUpdateView
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



]
