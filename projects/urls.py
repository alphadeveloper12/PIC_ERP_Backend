from django.urls import path
from .views import (
    ProjectCreateView,
    ProjectUpdateView,
    ProjectDetailView,
    ProjectListView,
    SubPhaseCreateView,
    SubPhaseListView,
    ProjectHealthView,
    ProjectHealthSummaryView
)

urlpatterns = [
    path('health_summary/', ProjectHealthSummaryView.as_view(), name='project-health-summary'),
    path('', ProjectListView.as_view(), name='project-list'),
    path('create/', ProjectCreateView.as_view(), name='project-create'),
    path('<int:pk>/', ProjectDetailView.as_view(), name='project-detail'),
    path('<int:pk>/update/', ProjectUpdateView.as_view(), name='project-update'),
    path('<int:pk>/health/', ProjectHealthView.as_view(), name='project-health'),
    
    # SubPhases (related to projects)
    path('subphase/list/', SubPhaseListView.as_view(), name='subphase-list'),
    path('subphase/create/', SubPhaseCreateView.as_view(), name='subphase-create'),
]
