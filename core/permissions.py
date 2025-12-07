# core/permissions.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Set

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.utils.functional import cached_property
from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import (
    UserRole,
    RolePermission,
    Permission,
    Grade,
    Employee,
)

User = get_user_model()


@dataclass(frozen=True)
class AccessRequirements:
    """Normalized access rules pulled from a DRF view."""
    any_codes: Set[str]
    all_codes: Set[str]
    min_grade_rank: Optional[int]  # lower rank = more senior (e.g., 1 is most senior)


def _normalize_iter(val: Optional[Iterable[str]]) -> Set[str]:
    if val is None:
        return set()
    return {str(v).strip() for v in val if str(v).strip()}


def _extract_requirements(view) -> AccessRequirements:
    """
    Supports:
      - required_permission: str
      - required_any_permissions: Iterable[str]
      - required_all_permissions: Iterable[str]
      - required_min_grade_code: str (e.g., 'G9')
      - required_min_grade_rank: int (lower is more senior)
    """
    # Back-compat: single required_permission
    single = getattr(view, "required_permission", None)
    any_codes = _normalize_iter(getattr(view, "required_any_permissions", None))
    all_codes = _normalize_iter(getattr(view, "required_all_permissions", None))

    if single:
        any_codes.add(str(single).strip())

    # Grade requirement (optional)
    min_grade_rank = getattr(view, "required_min_grade_rank", None)
    min_grade_code = getattr(view, "required_min_grade_code", None)

    if min_grade_rank is not None:
        try:
            min_grade_rank = int(min_grade_rank)
        except (TypeError, ValueError):
            min_grade_rank = None  # ignore invalid

    if min_grade_rank is None and min_grade_code:
        try:
            grade = Grade.objects.only("rank").get(code=min_grade_code)
            min_grade_rank = grade.rank
        except Grade.DoesNotExist:
            min_grade_rank = None  # ignore unknown code

    return AccessRequirements(any_codes=any_codes, all_codes=all_codes, min_grade_rank=min_grade_rank)


class _UserContext:
    """
    Lightweight aggregator for a user's permission codes and grade rank.
    Uses efficient ORM patterns to avoid N+1 queries. Cached per request.
    """

    def __init__(self, user: User) -> None:
        self.user = user

    @cached_property
    def permission_codes(self) -> Set[str]:
        """
        Collect permission codes via:
            User -> UserRole -> Role -> RolePermission -> Permission
        """
        if not self.user.is_authenticated:
            return set()

        # Prefetch in one go
        qs = (
            UserRole.objects
            .filter(user=self.user)
            .select_related("role")
            .prefetch_related("role__role_permissions__permission")
        )

        codes: Set[str] = set()
        for ur in qs:
            for rp in ur.role.role_permissions.all():
                # rp.permission is select_related in prefetch (via prefetch_related)
                perm = rp.permission
                if isinstance(perm, Permission):
                    codes.add(perm.code)
        return codes

    @cached_property
    def grade_rank(self) -> Optional[int]:
        """
        Lower number means more senior (rank=1 is top).
        """
        if not self.user.is_authenticated:
            return None
        try:
            employee: Employee = self.user.employee  # OneToOne
        except (ObjectDoesNotExist, AttributeError):
            return None

        if not employee or not employee.grade_id:
            return None

        try:
            return employee.grade.rank
        except (AttributeError, ObjectDoesNotExist):
            return None


class HasERPAccess(BasePermission):
    """
    Flexible RBAC guard.

    View attributes supported:
      - required_permission: str
      - required_any_permissions: Iterable[str]
      - required_all_permissions: Iterable[str]
      - required_min_grade_code: str (e.g., 'G9')
      - required_min_grade_rank: int (lower rank = more senior)

    Defaults:
      - If no requirements are specified, allow access.
      - If method is SAFE (GET/HEAD/OPTIONS) and no requirements, allow access.
    """

    def has_permission(self, request, view) -> bool:
        # Anonymous users fail unless explicitly allowed by the view permission_classes
        user = request.user
        req = _extract_requirements(view)

        # No explicit requirements? Allow read-only by default.
        if not req.any_codes and not req.all_codes and req.min_grade_rank is None:
            return request.method in SAFE_METHODS or user.is_authenticated

        ctx = _UserContext(user=user)
        if not user.is_authenticated:
            return False

        # Grade check (if any)
        if req.min_grade_rank is not None:
            user_rank = ctx.grade_rank
            # lower rank means more senior; require user_rank <= required_rank
            if user_rank is None or user_rank > req.min_grade_rank:
                return False

        # Permission checks
        user_codes = ctx.permission_codes

        if req.all_codes and not req.all_codes.issubset(user_codes):
            return False

        if req.any_codes and not (req.any_codes & user_codes):
            return False

        return True

    def has_object_permission(self, request, view, obj) -> bool:
        """
        By default, reuse the same logic. If you want object-level rules,
        set `required_object_any_permissions`, `required_object_all_permissions`,
        `required_object_min_grade_*` on the view, mirroring the class-level names.
        """
        user = request.user

        # If the view defines object-level requirements, evaluate them; else fall back.
        if hasattr(view, "required_object_any_permissions") or \
           hasattr(view, "required_object_all_permissions") or \
           hasattr(view, "required_object_min_grade_code") or \
           hasattr(view, "required_object_min_grade_rank"):

            # Build a lightweight proxy that exposes the object-level attributes
            class _ObjReqProxy:
                required_permission = None
                required_any_permissions = getattr(view, "required_object_any_permissions", None)
                required_all_permissions = getattr(view, "required_object_all_permissions", None)
                required_min_grade_code = getattr(view, "required_object_min_grade_code", None)
                required_min_grade_rank = getattr(view, "required_object_min_grade_rank", None)

            proxy = _ObjReqProxy()
            return self.has_permission(request, proxy)

        # Default behavior: defer to class-level has_permission
        return self.has_permission(request, view)
