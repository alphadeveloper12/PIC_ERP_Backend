# core/urls.py
from __future__ import annotations

from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from .views import (
    # Companies
    CompanyCreateView,
    CompanyListView,

    # Profile (backward-compatible over Employee)
    ProfileCreateView,
    ProfileListView,

    # Departments
    DepartmentCreateView,
    DepartmentListView,

    # Roles
    RoleCreateView,
    RoleListView,

    # Permissions
    PermissionCreateView,
    PermissionListView,
    RolePermissionAssignView,

    # User ↔ Department/Role
    UserRoleAssignView,
    UserRolesListView,

    # Auth
    MeView,

    # Optional new entities (enable as needed)
    LocationCreateView,
    LocationListView,
    GradeCreateView,
    GradeListView,
    JobFamilyCreateView,
    JobFamilyListView,
    JobTitleCreateView,
    JobTitleListView,
    PositionCreateView,
    PositionListView,
    EmployeeCreateView,
    EmployeeListView,
)

app_name = "core"

urlpatterns = [
    # ------------------------------------------------------------------
    # Companies
    # ------------------------------------------------------------------
    path("companies/", CompanyListView.as_view(), name="company-list"),
    path("companies/create/", CompanyCreateView.as_view(), name="company-create"),

    # ------------------------------------------------------------------
    # Profiles (shim over Employee)
    # ------------------------------------------------------------------
    path("profiles/", ProfileListView.as_view(), name="profile-list"),
    path("profiles/create/", ProfileCreateView.as_view(), name="profile-create"),

    # ------------------------------------------------------------------
    # Departments
    # ------------------------------------------------------------------
    path("departments/", DepartmentListView.as_view(), name="department-list"),
    path("departments/create/", DepartmentCreateView.as_view(), name="department-create"),

    # ------------------------------------------------------------------
    # Roles
    # ------------------------------------------------------------------
    path("roles/", RoleListView.as_view(), name="role-list"),
    path("roles/create/", RoleCreateView.as_view(), name="role-create"),

    # ------------------------------------------------------------------
    # Permissions
    # ------------------------------------------------------------------
    path("permissions/", PermissionListView.as_view(), name="permission-list"),
    path("permissions/create/", PermissionCreateView.as_view(), name="permission-create"),
    path("roles/assign-permissions/", RolePermissionAssignView.as_view(), name="role-permissions-assign"),

    # ------------------------------------------------------------------
    # User ↔ Department/Role
    # ------------------------------------------------------------------
    path("user-roles/", UserRolesListView.as_view(), name="user-role-list"),
    path("user-roles/assign/", UserRoleAssignView.as_view(), name="user-role-assign"),

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------
    path("auth/me/", MeView.as_view(), name="auth-me"),

    # ------------------------------------------------------------------
    # Optional: new entities (locations, grades, job families/titles, positions, employees)
    # ------------------------------------------------------------------
    path("locations/", LocationListView.as_view(), name="location-list"),
    path("locations/create/", LocationCreateView.as_view(), name="location-create"),

    path("grades/", GradeListView.as_view(), name="grade-list"),
    path("grades/create/", GradeCreateView.as_view(), name="grade-create"),

    path("job-families/", JobFamilyListView.as_view(), name="jobfamily-list"),
    path("job-families/create/", JobFamilyCreateView.as_view(), name="jobfamily-create"),

    path("job-titles/", JobTitleListView.as_view(), name="jobtitle-list"),
    path("job-titles/create/", JobTitleCreateView.as_view(), name="jobtitle-create"),

    path("positions/", PositionListView.as_view(), name="position-list"),
    path("positions/create/", PositionCreateView.as_view(), name="position-create"),

    path("employees/", EmployeeListView.as_view(), name="employee-list"),
    path("employees/create/", EmployeeCreateView.as_view(), name="employee-create"),
]

urlpatterns = format_suffix_patterns(urlpatterns)