from django.urls import path
from .views import XerImportAPIView

urlpatterns = [
    path('planning/<int:planning_id>/import-xer/', XerImportAPIView.as_view(), name='import-xer'),
    # path('api/xer-imports/<int:id>/status/', XerImportJobStatusAPIView.as_view(), name='xer-import-status'),
]