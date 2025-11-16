from django.urls import path
from .views import UploadPrimaveraView, ProjectHierarchyView

urlpatterns = [
    path('upload/', UploadPrimaveraView.as_view(), name='upload-primavera'),
    path('projects/', ProjectHierarchyView.as_view(), name='project-hierarchy'),
]