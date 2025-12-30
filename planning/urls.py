from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import P6ActivityViewSet, PrimaveraSheetViewSet, PrimaveraFeedbackView

router = DefaultRouter()
router.register(r'p6-activities', P6ActivityViewSet, basename='p6-activities')
router.register(r'primavera-sheets', PrimaveraSheetViewSet, basename='primavera-sheets')

urlpatterns = [
    path('feedback/', PrimaveraFeedbackView.as_view(), name='primavera-feedback'),
    path('', include(router.urls)),
]