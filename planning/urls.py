from django.urls import path
from .views import UploadPrimaveraView, ProjectHierarchyView, UploadP6AndMatch

urlpatterns = [
    path('upload/', UploadPrimaveraView.as_view(), name='upload-primavera'),
    path('projects/', ProjectHierarchyView.as_view(), name='project-hierarchy'),
    path("upload-planning/", UploadP6AndMatch.as_view(), name="upload-planning"),
]