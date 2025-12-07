# core/admin.py
from __future__ import annotations

from typing import Tuple
from django.contrib import admin
from django.db.models import QuerySet

from .models import (
    Company,
    Location,
    Grade,
    Department,
    JobFamily,
    JobTitle,
    Position,
    Employee,
    Permission,
    Role,
    RolePermission,
    UserRole,
    Currency
)


# ---------------------------------------------------------------------
# GENERIC MIXIN
# ---------------------------------------------------------------------
class ReadOnlyTSMixin(admin.ModelAdmin):
    readonly_fields: Tuple[str, str] = ("created_at", "updated_at")


# ---------------------------------------------------------------------
# VALID INLINES
# ---------------------------------------------------------------------
class RolePermissionInline(admin.TabularInline):
    model = RolePermission
    extra = 0
    autocomplete_fields = ("permission",)
    verbose_name = "Permission"
    verbose_name_plural = "Permissions"


class PositionInline(admin.TabularInline):
    """Valid under Department (FK Position.department)."""
    model = Position
    extra = 0
    fields = ("job_title", "grade", "location", "reports_to", "is_managerial", "is_active")
    autocomplete_fields = ("job_title", "grade", "location", "reports_to")


class DepartmentInline(admin.TabularInline):
    """Valid under Company (FK Department.company)."""
    model = Department
    extra = 0
    fields = ("name", "parent", "description")
    autocomplete_fields = ("parent",)


class LocationInline(admin.TabularInline):
    """Valid under Company (FK Location.company)."""
    model = Location
    extra = 0
    fields = ("name", "address")


# NOTE: Removed UserRoleInline from EmployeeAdmin — UserRole has FK to User, not Employee.


# ---------------------------------------------------------------------
# COMPANY / LOCATION
# ---------------------------------------------------------------------
@admin.register(Company)
class CompanyAdmin(ReadOnlyTSMixin):
    list_display = ("name", "code", "country", "city", "is_active")
    list_filter = ("is_active", "country", "city")
    search_fields = ("name", "code", "address")
    ordering = ("name",)
    inlines = [DepartmentInline, LocationInline]


@admin.register(Location)
class LocationAdmin(ReadOnlyTSMixin):
    list_display = ("name", "company", "address")
    list_filter = ("company",)
    search_fields = ("name", "address", "company__name")
    ordering = ("company__name", "name")
    autocomplete_fields = ("company",)

    def get_queryset(self, request) -> QuerySet[Location]:
        return super().get_queryset(request).select_related("company")


# ---------------------------------------------------------------------
# GRADE
# ---------------------------------------------------------------------
@admin.register(Grade)
class GradeAdmin(ReadOnlyTSMixin):
    list_display = ("code", "label", "rank", "approval_limit")
    list_filter = ("rank",)
    search_fields = ("code", "label")
    ordering = ("rank",)


# ---------------------------------------------------------------------
# DEPARTMENT
# ---------------------------------------------------------------------
@admin.register(Department)
class DepartmentAdmin(ReadOnlyTSMixin):
    list_display = ("name", "company", "parent")
    list_filter = ("company",)
    search_fields = ("name", "company__name", "parent__name")
    ordering = ("company__name", "name")
    autocomplete_fields = ("company", "parent")
    inlines = [PositionInline]  # <-- positions now inline under Department

    def get_queryset(self, request) -> QuerySet[Department]:
        return super().get_queryset(request).select_related("company", "parent")


# ---------------------------------------------------------------------
# JOB FAMILY / TITLE
# ---------------------------------------------------------------------
@admin.register(JobFamily)
class JobFamilyAdmin(ReadOnlyTSMixin):
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(JobTitle)
class JobTitleAdmin(ReadOnlyTSMixin):
    list_display = ("name", "job_family", "default_grade")
    list_filter = ("job_family", "default_grade")
    search_fields = ("name", "job_family__name", "default_grade__code")
    ordering = ("name",)
    autocomplete_fields = ("job_family", "default_grade")

    def get_queryset(self, request) -> QuerySet[JobTitle]:
        return super().get_queryset(request).select_related("job_family", "default_grade")


# ---------------------------------------------------------------------
# POSITION
# ---------------------------------------------------------------------
@admin.register(Position)
class PositionAdmin(ReadOnlyTSMixin):
    list_display = ("job_title", "department", "grade", "location", "reports_to", "is_managerial", "is_active")
    list_filter = ("is_active", "is_managerial", "department__company", "department", "grade", "location")
    search_fields = ("job_title__name", "department__name", "department__company__name", "location__name")
    ordering = ("department__company__name", "department__name", "job_title__name")
    autocomplete_fields = ("department", "job_title", "grade", "location", "reports_to")
    actions = ("activate_positions", "deactivate_positions")

    def get_queryset(self, request) -> QuerySet[Position]:
        return (
            super()
            .get_queryset(request)
            .select_related("department", "department__company", "job_title", "grade", "location", "reports_to")
        )

    @admin.action(description="Activate selected positions")
    def activate_positions(self, request, queryset: QuerySet[Position]) -> None:
        queryset.update(is_active=True)

    @admin.action(description="Deactivate selected positions")
    def deactivate_positions(self, request, queryset: QuerySet[Position]) -> None:
        queryset.update(is_active=False)


# ---------------------------------------------------------------------
# EMPLOYEE
# ---------------------------------------------------------------------
@admin.register(Employee)
class EmployeeAdmin(ReadOnlyTSMixin):
    list_display = ("display_name", "company", "position", "grade", "work_location", "hire_date")
    list_filter = ("company", "grade", "work_location")
    search_fields = (
        "first_name",
        "last_name",
        "user__username",
        "user__email",
        "company__name",
        "position__job_title__name",
    )
    ordering = ("last_name", "first_name")
    autocomplete_fields = ("user", "company", "position", "grade", "work_location")

    def get_queryset(self, request) -> QuerySet[Employee]:
        return (
            super()
            .get_queryset(request)
            .select_related("user", "company", "position", "position__department", "position__job_title", "grade", "work_location")
        )

    @admin.display(description="Name")
    def display_name(self, obj: Employee) -> str:
        return f"{obj.first_name} {obj.last_name}".strip()


# ---------------------------------------------------------------------
# PERMISSIONS / ROLES / USER-ROLES
# ---------------------------------------------------------------------
@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("code", "description")
    search_fields = ("code", "description")
    ordering = ("code",)


@admin.register(Role)
class RoleAdmin(ReadOnlyTSMixin):
    list_display = ("name", "department")
    list_filter = ("department__company", "department")
    search_fields = ("name", "department__name", "department__company__name")
    ordering = ("department__company__name", "department__name", "name")
    autocomplete_fields = ("department",)
    inlines = [RolePermissionInline]

    def get_queryset(self, request) -> QuerySet[Role]:
        return super().get_queryset(request).select_related("department", "department__company")


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ("role", "permission")
    list_filter = ("role__department__company", "role__department")
    search_fields = ("role__name", "permission__code")
    ordering = ("role__department__company__name", "role__name", "permission__code")
    autocomplete_fields = ("role", "permission")

    def get_queryset(self, request) -> QuerySet[RolePermission]:
        return super().get_queryset(request).select_related("role", "permission", "role__department", "role__department__company")


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("user", "department", "role", "created_at")
    list_filter = ("department__company", "department", "role")
    search_fields = ("user__username", "user__email", "department__name", "role__name")
    ordering = ("user__username", "department__name", "role__name")
    autocomplete_fields = ("user", "department", "role")

    def get_queryset(self, request) -> QuerySet[UserRole]:
        return super().get_queryset(request).select_related("user", "department", "role")


# ---------------------------------------------------------------------
# BRANDING
# ---------------------------------------------------------------------
admin.site.site_header = "ERP Admin"
admin.site.site_title = "ERP Admin"
admin.site.index_title = "Administration"



admin.site.register(Currency)