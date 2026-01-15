from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DepartmentViewSet, TaskViewSet, DocumentViewSet, ProjectTeamViewSet, AccessPolicyViewSet

router = DefaultRouter()
router.register(r'departments', DepartmentViewSet)
router.register(r'tasks', TaskViewSet)
router.register(r'documents', DocumentViewSet)
router.register(r'team', ProjectTeamViewSet)
router.register(r'access-policies', AccessPolicyViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
