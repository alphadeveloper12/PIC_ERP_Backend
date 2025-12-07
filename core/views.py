# core/views.py
from __future__ import annotations

from typing import Any, Dict, List

from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Company,
    Department,
    Role,
    Permission,
    RolePermission,
    UserRole,
    Location,
    Grade,
    JobFamily,
    JobTitle,
    Position,
    Employee,
)
from .serializers import (
    CompanySerializer,
    ProfileSerializer,           # shim over Employee
    DepartmentSerializer,
    RoleSerializer,
    PermissionSerializer,
    UserRoleSerializer,
    CreateRolePermissionsSerializer,
    UserMeSerializer,

    # New but optional endpoints if you need them later
    LocationSerializer,
    GradeSerializer,
    JobFamilySerializer,
    JobTitleSerializer,
    PositionSerializer,
    EmployeeSerializer,
)

User = get_user_model()


# =============================================================================
# COMPANY
# =============================================================================
class CompanyCreateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, **kwargs) -> JsonResponse:
        try:
            serializer = CompanySerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return JsonResponse(
                {
                    "status": "success",
                    "message": "Company created successfully",
                    "data": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as exc:
            return JsonResponse(
                {
                    "status": "failed",
                    "message": str(exc) or "Something went wrong...",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class CompanyListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, **kwargs) -> JsonResponse:
        try:
            qs = Company.objects.all().order_by("name")
            serializer = CompanySerializer(qs, many=True)
            return JsonResponse(
                {"status": "success", "message": None, "data": serializer.data},
                status=status.HTTP_200_OK,
            )
        except Exception as exc:
            return JsonResponse(
                {"status": "failed", "message": str(exc) or "Something went wrong...", "data": None},
                status=status.HTTP_400_BAD_REQUEST,
            )


# =============================================================================
# PROFILE (Backward-compatible over Employee)
# =============================================================================
class ProfileCreateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, **kwargs) -> JsonResponse:
        try:
            serializer = ProfileSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return JsonResponse(
                {
                    "status": "success",
                    "message": "Profile created successfully",
                    "data": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as exc:
            return JsonResponse(
                {"status": "failed", "message": str(exc) or "Something went wrong...", "data": None},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ProfileListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, **kwargs) -> JsonResponse:
        try:
            qs = (
                Employee.objects.select_related("user", "company", "position", "grade", "work_location")
                .order_by("last_name", "first_name")
            )
            serializer = ProfileSerializer(qs, many=True)
            return JsonResponse(
                {"status": "success", "message": None, "data": serializer.data},
                status=status.HTTP_200_OK,
            )
        except Exception as exc:
            return JsonResponse(
                {"status": "failed", "message": str(exc) or "Something went wrong...", "data": None},
                status=status.HTTP_400_BAD_REQUEST,
            )


# =============================================================================
# DEPARTMENTS
# =============================================================================
class DepartmentCreateView(generics.CreateAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [AllowAny]


class DepartmentListView(generics.ListAPIView):
    serializer_class = DepartmentSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return (
            Department.objects.select_related("company", "parent")
            .all()
            .order_by("company__name", "name")
        )


# =============================================================================
# ROLES
# =============================================================================
class RoleCreateView(generics.CreateAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [AllowAny]


class RoleListView(generics.ListAPIView):
    serializer_class = RoleSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return (
            Role.objects.select_related("department")
            .prefetch_related("role_permissions__permission")
            .order_by("department__name", "name")
        )


# =============================================================================
# PERMISSIONS
# =============================================================================
class PermissionCreateView(generics.CreateAPIView):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [AllowAny]


class PermissionListView(generics.ListAPIView):
    queryset = Permission.objects.all().order_by("code")
    serializer_class = PermissionSerializer
    permission_classes = [AllowAny]


# =============================================================================
# ROLE ↔ PERMISSIONS ASSIGNMENT
# =============================================================================
class RolePermissionAssignView(generics.GenericAPIView):
    serializer_class = CreateRolePermissionsSerializer
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request, *args, **kwargs) -> Response:
        data_serializer = self.get_serializer(data=request.data)
        data_serializer.is_valid(raise_exception=True)

        role_id: int = data_serializer.validated_data["role_id"]
        codes: List[str] = data_serializer.validated_data["permission_codes"]

        role = get_object_or_404(Role, id=role_id)
        perms = list(Permission.objects.filter(code__in=codes))

        # Idempotent assign
        created_count = 0
        for perm in perms:
            _, created = RolePermission.objects.get_or_create(role=role, permission=perm)
            if created:
                created_count += 1

        return Response(
            {"message": "Permissions assigned successfully", "created": created_count, "role_id": role.id},
            status=status.HTTP_200_OK,
        )


# =============================================================================
# USER ↔ DEPARTMENT/ROLE ASSIGNMENT
# =============================================================================
class UserRoleAssignView(generics.CreateAPIView):
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer) -> None:
        # enforce uniqueness at DB level; serializer.save() will raise if violation
        serializer.save()


class UserRolesListView(generics.ListAPIView):
    serializer_class = UserRoleSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return (
            UserRole.objects.select_related("user", "department", "role")
            .all()
            .order_by("user__username", "department__name", "role__name")
        )


# =============================================================================
# AUTH / ME
# =============================================================================
class MeView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        serializer = UserMeSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


# =============================================================================
# OPTIONAL: Additional endpoints for new entities (enable when ready)
# =============================================================================

class LocationCreateView(generics.CreateAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [AllowAny]


class LocationListView(generics.ListAPIView):
    queryset = Location.objects.select_related("company").all().order_by("company__name", "name")
    serializer_class = LocationSerializer
    permission_classes = [AllowAny]


class GradeCreateView(generics.CreateAPIView):
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer
    permission_classes = [AllowAny]


class GradeListView(generics.ListAPIView):
    queryset = Grade.objects.all().order_by("rank")
    serializer_class = GradeSerializer
    permission_classes = [AllowAny]


class JobFamilyCreateView(generics.CreateAPIView):
    queryset = JobFamily.objects.all()
    serializer_class = JobFamilySerializer
    permission_classes = [AllowAny]


class JobFamilyListView(generics.ListAPIView):
    queryset = JobFamily.objects.all().order_by("name")
    serializer_class = JobFamilySerializer
    permission_classes = [AllowAny]


class JobTitleCreateView(generics.CreateAPIView):
    queryset = JobTitle.objects.all()
    serializer_class = JobTitleSerializer
    permission_classes = [AllowAny]


class JobTitleListView(generics.ListAPIView):
    queryset = JobTitle.objects.select_related("job_family", "default_grade").all().order_by("name")
    serializer_class = JobTitleSerializer
    permission_classes = [AllowAny]


class PositionCreateView(generics.CreateAPIView):
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    permission_classes = [AllowAny]


class PositionListView(generics.ListAPIView):
    serializer_class = PositionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return (
            Position.objects.select_related(
                "department", "job_title", "grade", "location", "reports_to"
            )
            .all()
            .order_by("department__name", "job_title__name")
        )


class EmployeeCreateView(generics.CreateAPIView):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [AllowAny]


class EmployeeListView(generics.ListAPIView):
    serializer_class = EmployeeSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return (
            Employee.objects.select_related("user", "company", "position", "grade", "work_location")
            .all()
            .order_by("last_name", "first_name")
        )
