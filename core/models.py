# core/models.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Literal, Iterable
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


# ---------------------------------------------------------------------
# ABSTRACTS
# ---------------------------------------------------------------------
class TimeStampedModel(models.Model):
    """Reusable timestamp fields."""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True


# ---------------------------------------------------------------------
# COMPANY / LOCATION
# ---------------------------------------------------------------------
class Company(TimeStampedModel):
    """Represents a company or branch within a group."""
    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=50, unique=True)
    image = models.URLField(null=True, blank=True)
    address = models.TextField(blank=True)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name


class Location(TimeStampedModel):
    """A specific physical or project site location."""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="locations")
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True)

    class Meta:
        unique_together = ("company", "name")

    def __str__(self) -> str:
        return f"{self.company.name} - {self.name}"


# ---------------------------------------------------------------------
# GRADE & JOB STRUCTURE
# ---------------------------------------------------------------------
class Grade(TimeStampedModel):
    """Corporate grade ladder (Director, Manager, Engineer...)."""
    code = models.CharField(max_length=10, unique=True)  # e.g., G12
    label = models.CharField(max_length=100)  # e.g., "Director"
    rank = models.PositiveSmallIntegerField(default=1)
    approval_limit = models.DecimalField(max_digits=18, decimal_places=2, default=0)

    class Meta:
        ordering = ["rank"]

    def __str__(self) -> str:
        return f"{self.code} - {self.label}"


class Department(TimeStampedModel):
    """Departments within a company."""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="departments")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT, related_name="children")

    class Meta:
        unique_together = ("company", "name")

    def __str__(self) -> str:
        return self.name


class JobFamily(TimeStampedModel):
    """Categorizes job titles by discipline (Engineering, Finance, QA/QC...)."""
    name = models.CharField(max_length=100, unique=True)

    def __str__(self) -> str:
        return self.name


class JobTitle(TimeStampedModel):
    """Canonical job titles tied to job families."""
    name = models.CharField(max_length=150, unique=True)
    job_family = models.ForeignKey(JobFamily, on_delete=models.PROTECT, related_name="titles")
    default_grade = models.ForeignKey(Grade, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self) -> str:
        return self.name


class Position(TimeStampedModel):
    """Represents an actual seat or post within a department."""
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="positions")
    job_title = models.ForeignKey(JobTitle, on_delete=models.PROTECT, related_name="positions")
    grade = models.ForeignKey(Grade, on_delete=models.PROTECT)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    reports_to = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="subordinates")
    is_managerial = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["department", "grade"]),
            models.Index(fields=["reports_to"]),
        ]

    def clean(self) -> None:
        if self.reports_to_id == self.id:
            raise ValidationError("A position cannot report to itself.")

    def __str__(self) -> str:
        return f"{self.job_title.name} @ {self.department.name}"


# ---------------------------------------------------------------------
# EMPLOYEE / PROFILE
# ---------------------------------------------------------------------
class Employee(TimeStampedModel):
    """Core employee profile linked to a Django User."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="employee")
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="employees")
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True)
    grade = models.ForeignKey(Grade, on_delete=models.SET_NULL, null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    nationality = models.CharField(max_length=100, blank=True)
    hire_date = models.DateField(null=True, blank=True)
    work_location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"


# ---------------------------------------------------------------------
# PERMISSIONS / RBAC
# ---------------------------------------------------------------------
class Permission(TimeStampedModel):
    code = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.code


class Role(TimeStampedModel):
    """Organizational role within a department, tied to a job title."""
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="roles")
    description = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.department.name})"


class RolePermission(TimeStampedModel):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="role_permissions")
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("role", "permission")

    def __str__(self) -> str:
        return f"{self.role.name} → {self.permission.code}"


class UserRole(TimeStampedModel):
    """Links a User/Employee to roles within departments."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_roles")
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("user", "department", "role")

    def __str__(self) -> str:
        return f"{self.user.username} → {self.department.name} ({self.role.name})"


# class VillaType(models.Model):
#     name = models.CharField(max_length=100)  # e.g., "3-Bedroom Villa"
#     description = models.TextField(blank=True, null=True)
#     m2 = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)  # Size in square meters
#     price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
#
#     def __str__(self):
#         return self.name
#
#
# class VillaPlan(models.Model):
#     subphase = models.ForeignKey(SubPhase, related_name='villa_plans', on_delete=models.CASCADE)
#     villa_type = models.ForeignKey(VillaType, related_name='villa_plans', on_delete=models.CASCADE)
#     estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
#     quantity = models.PositiveIntegerField()  # Number of villas of this type in this phase
#
#     def __str__(self):
#         return f"{self.villa_type.name} - {self.subphase.name}"

class Currency(models.Model):
    code = models.CharField(max_length=10, unique=True)  # e.g., "USD"
    symbol = models.CharField(max_length=5)  # e.g., "$"
    exchange_rate = models.DecimalField(max_digits=12, decimal_places=6)

    def __str__(self):
        return self.code