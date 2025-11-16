# core/models.py
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True


class Company(TimeStampedModel):
    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=50, unique=True)
    image = models.URLField(null=True, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Profile(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="profiles")
    role = models.CharField(max_length=100, blank=True)  # e.g. PM, QS, Admin

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} @ {self.company}"


class Currency(models.Model):
    code = models.CharField(max_length=10, unique=True)  # e.g., "USD"
    symbol = models.CharField(max_length=5)  # e.g., "$"
    exchange_rate = models.DecimalField(max_digits=12, decimal_places=6)

    def __str__(self):
        return self.code


class Department(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Role(models.Model):
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="roles")

    # Optional: add metadata for permission definition
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.department.name})"


# Mapping table: One user can belong to many departments with many roles
class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_roles")
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("user", "department", "role")

    def __str__(self):
        return f"{self.user.username} → {self.department.name} ({self.role.name})"


# Define permissions for each role
class Permission(models.Model):
    code = models.CharField(max_length=100, unique=True)   # example: "can_create_invoice"
    description = models.CharField(max_length=255)

    def __str__(self):
        return self.code


class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="permissions")
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("role", "permission")


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

