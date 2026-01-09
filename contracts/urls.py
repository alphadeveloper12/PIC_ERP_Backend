from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ConstructionContractViewSet

router = DefaultRouter()
router.register(r'contracts', ConstructionContractViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
