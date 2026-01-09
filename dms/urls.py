from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DepartmentViewSet, TaskViewSet, DocumentViewSet

router = DefaultRouter()
router.register(r'departments', DepartmentViewSet)
router.register(r'tasks', TaskViewSet)
router.register(r'documents', DocumentViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
