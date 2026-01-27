# core/serializers.py
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Set, Type

from django.contrib.auth import get_user_model
from django.db.models import Prefetch, QuerySet
from rest_framework import serializers

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
)

User = get_user_model()


# ---------------------------------------------------------------------
# BASIC SERIALIZERS
# ---------------------------------------------------------------------
class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = "__all__"


class LocationSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = Location
        fields = ["id", "name", "address", "company", "company_name", "created_at", "updated_at"]


class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = ["id", "code", "label", "rank", "approval_limit", "created_at", "updated_at"]


class JobFamilySerializer(serializers.ModelSerializer):
    class Meta:
        model = JobFamily
        fields = ["id", "name", "created_at", "updated_at"]


class JobTitleSerializer(serializers.ModelSerializer):
    job_family_name = serializers.CharField(source="job_family.name", read_only=True)
    default_grade_code = serializers.CharField(source="default_grade.code", read_only=True)

    class Meta:
        model = JobTitle
        fields = [
            "id",
            "name",
            "job_family",
            "job_family_name",
            "default_grade",
            "default_grade_code",
            "created_at",
            "updated_at",
        ]


class DepartmentSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)
    parent_name = serializers.CharField(source="parent.name", read_only=True)

    class Meta:
        model = Department
        fields = [
            "id",
            "company",
            "company_name",
            "name",
            "description",
            "parent",
            "parent_name",
            "created_at",
            "updated_at",
        ]


class PositionSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)
    job_title_name = serializers.CharField(source="job_title.name", read_only=True)
    grade_code = serializers.CharField(source="grade.code", read_only=True)
    location_name = serializers.CharField(source="location.name", read_only=True)
    reports_to_title = serializers.CharField(source="reports_to.job_title.name", read_only=True)

    class Meta:
        model = Position
        fields = [
            "id",
            "department",
            "department_name",
            "job_title",
            "job_title_name",
            "grade",
            "grade_code",
            "location",
            "location_name",
            "reports_to",
            "reports_to_title",
            "is_managerial",
            "is_active",
            "created_at",
            "updated_at",
        ]


# ---------------------------------------------------------------------
# EMPLOYEE / PROFILE (Backwards-compatible with your old Profile views)
# ---------------------------------------------------------------------
class EmployeeSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source="user.username", read_only=True)
    company_name = serializers.CharField(source="company.name", read_only=True)
    position_title = serializers.CharField(source="position.job_title.name", read_only=True, default=None)
    grade_code = serializers.CharField(source="grade.code", read_only=True, default=None)
    work_location_name = serializers.CharField(source="work_location.name", read_only=True, default=None)

    class Meta:
        model = Employee
        fields = [
            "id",
            "user",
            "user_username",
            "company",
            "company_name",
            "position",
            "position_title",
            "grade",
            "grade_code",
            "first_name",
            "last_name",
            "nationality",
            "hire_date",
            "work_location",
            "work_location_name",
            "created_at",
            "updated_at",
        ]


class ProfileSerializer(serializers.ModelSerializer):
    # Backward-compat with old API: accept a free-text "role" on write,
    # and expose "role_display" from the current Position/JobTitle on read.
    role: serializers.CharField = serializers.CharField(
        required=False, allow_blank=True, write_only=True
    )
    role_display: serializers.SerializerMethodField = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Employee
        fields = [
            "id",
            "user",
            "company",
            "position",
            "grade",
            "first_name",
            "last_name",
            "nationality",
            "hire_date",
            "work_location",
            "created_at",
            "updated_at",
            # legacy compatibility fields
            "role",          # write-only shim (ignored on save)
            "role_display",  # read-only, derived from Position/JobTitle
        ]
        read_only_fields = ("created_at", "updated_at")

    def get_role_display(self, obj: Employee) -> str:
        try:
            return obj.position.job_title.name if obj.position and obj.position.job_title else ""
        except Exception:
            return ""

    def create(self, validated_data: dict) -> Employee:
        # Ignore legacy "role" free-text; real role mapping is via UserRole
        validated_data.pop("role", None)
        return super().create(validated_data)

    def update(self, instance: Employee, validated_data: dict) -> Employee:
        validated_data.pop("role", None)
        return super().update(instance, validated_data)


# ---------------------------------------------------------------------
# PERMISSIONS / ROLES
# ---------------------------------------------------------------------
class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = "__all__"


class RoleSerializer(serializers.ModelSerializer):
    """
    Mirrors your previous serializer shape: includes `permissions` as a flat list of codes.
    """
    permissions = serializers.SerializerMethodField()
    department_name = serializers.CharField(source="department.name", read_only=True)

    class Meta:
        model = Role
        fields = ["id", "name", "description", "department", "department_name", "permissions"]

    def get_permissions(self, obj: Role) -> List[str]:
        # Defensive prefetch for performance if viewset didn't add it
        qs: QuerySet[RolePermission] = obj.role_permissions.all().select_related("permission")
        return [rp.permission.code for rp in qs]


class RolePermissionAssignSerializer(serializers.Serializer):
    """Optional: a stricter, typed version of your input contract."""
    role_id = serializers.IntegerField()
    permission_codes = serializers.ListField(child=serializers.CharField(allow_blank=False), allow_empty=False)

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        role_id: int = attrs["role_id"]
        codes: List[str] = attrs["permission_codes"]

        if not Role.objects.filter(id=role_id).exists():
            raise serializers.ValidationError("Role not found.")

        missing = set(codes) - set(Permission.objects.filter(code__in=codes).values_list("code", flat=True))
        if missing:
            raise serializers.ValidationError(f"Unknown permission codes: {', '.join(sorted(missing))}")

        return attrs


# Keep the original name your views import
CreateRolePermissionsSerializer = RolePermissionAssignSerializer


class UserRoleSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)
    role_name = serializers.CharField(source="role.name", read_only=True)

    class Meta:
        model = UserRole
        fields = ["id", "user", "department", "department_name", "role", "role_name", "created_at", "updated_at"]


# ---------------------------------------------------------------------
# USER-CENTRIC SERIALIZERS (for /auth/me)
# ---------------------------------------------------------------------
class UserDepartmentRoleSerializer(serializers.ModelSerializer):
    """
    For a given Department, return the roles the current user holds and
    the permission codes associated with each role.
    """
    roles = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = ["id", "name", "roles"]

    def get_roles(self, dept: Department) -> List[Dict[str, Any]]:
        user: User = self.context["user"]

        # Prefetch for efficiency
        qs: QuerySet[UserRole] = (
            UserRole.objects.filter(user=user, department=dept)
            .select_related("role")
            .prefetch_related(
                Prefetch(
                    "role__role_permissions",
                    queryset=RolePermission.objects.select_related("permission"),
                )
            )
        )

        result: List[Dict[str, Any]] = []
        for ur in qs:
            perms = [rp.permission.code for rp in ur.role.role_permissions.all()]
            result.append(
                {
                    "role_id": ur.role.id,
                    "role_name": ur.role.name,
                    "permissions": perms,
                }
            )
        return result


class UserMeSerializer(serializers.ModelSerializer):
    """
    Mirrors your previous response:
    - id, username, email
    - departments: list of departments with the user's roles and permissions
    - permissions: Flat list of all permissions (legacy/global fallback)
    - project_permissions: Dict of {project_id: [permissions]}
    """
    departments = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    project_permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "departments", "permissions", "project_permissions"]

    def get_departments(self, user: User) -> List[Dict[str, Any]]:
        # Collect unique departments from user's role assignments.
        dept_ids: Set[int] = set(
            UserRole.objects.filter(user=user).values_list("department_id", flat=True)
        )
        depts: QuerySet[Department] = Department.objects.filter(id__in=dept_ids)

        return UserDepartmentRoleSerializer(
            depts,
            many=True,
            context={"user": user},
        ).data

    def get_permissions(self, user: User) -> List[str]:
        """
        Returns a flat list of all permissions the user has across all departments and projects.
        This serves as a fallback for the frontend 'hasAnyPermission' check when no project is active.
        """
        # 1. Get Core permissions (Legacy)
        core_perms = set()
        for ur in UserRole.objects.filter(user=user).select_related('role'):
             for rp in ur.role.role_permissions.all():
                 core_perms.add(rp.permission.code)
        
        # 2. Get DMS permissions
        try:
            from dms.models import UserDepartmentRole, AccessPolicy
            dms_perms = set()
            
            # Find all roles assigned to user
            user_dms_roles = UserDepartmentRole.objects.filter(user=user)
            
            for ur in user_dms_roles:
                # Find matching policy
                # Policy matches: Project + Department + Role
                # If policy for specific project exists, use it.
                # If policy is Global (project=None), it might apply? 
                # For now, let's just grab the policy that matches the assignment.
                
                # If UserDepartmentRole has a project, look for that project's policy
                # If UserDepartmentRole has project=None (Global Role?), look for Global Policy?
                
                # Let's try to match exactly first
                policies = AccessPolicy.objects.filter(
                    department=ur.department,
                    role=ur.role
                )
                
                if ur.project:
                    policies = policies.filter(project=ur.project)
                else:
                    # User has global role in department... 
                    # Does that mean they get global policy? or all project policies?
                    # Let's assume global policy
                    policies = policies.filter(project__isnull=True)
                
                for policy in policies:
                    for p_code in policy.permissions:
                        dms_perms.add(p_code)
                        
            return list(core_perms.union(dms_perms))
            
        except ImportError:
            # Fallback if dms app is not available (though it should be)
            return list(core_perms)
        except Exception as e:
            # Log error?
            return list(core_perms)

    def get_project_permissions(self, user: User) -> Dict[str, List[str]]:
        """
        Returns a dict mapping project_id (as string) to a list of permission codes.
        Used by the frontend to enforce project-scoped security.
        """
        result = {}
        
        try:
            from dms.models import UserDepartmentRole, AccessPolicy
            
            # Find all user roles that are attached to a project
            user_project_roles = UserDepartmentRole.objects.filter(
                user=user, 
                project__isnull=False
            ).select_related('project', 'department')
            
            for ur in user_project_roles:
                project_id = str(ur.project.id)
                
                # Find specific policy for this project/dept/role
                try:
                    policy = AccessPolicy.objects.get(
                        project=ur.project,
                        department=ur.department,
                        role=ur.role
                    )
                    if project_id not in result:
                        result[project_id] = []
                    result[project_id].extend(policy.permissions)
                    
                except AccessPolicy.DoesNotExist:
                     # Maybe fallback to global policy? 
                     # Usually specific project policy overrides or is required.
                     # Let's check for a global template assignment?
                     # dms/utils.py seed function copies templates to projects.
                     # So we expect a project-specific policy to exist.
                     pass
            
            # Deduplicate per project
            for pid in result:
                result[pid] = list(set(result[pid]))
                
        except ImportError:
            pass
            
        return result
