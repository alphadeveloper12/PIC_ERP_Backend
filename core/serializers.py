from .models import *
from rest_framework import serializers


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = '__all__'


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = "__all__"


class RoleSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = ["id", "name", "description", "department", "permissions"]

    def get_permissions(self, obj):
        return [rp.permission.code for rp in obj.role_permissions.all()]


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = "__all__"


class UserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRole
        fields = "__all__"


class CreateRolePermissionsSerializer(serializers.Serializer):
    role_id = serializers.IntegerField()
    permission_codes = serializers.ListField(child=serializers.CharField())


class UserDepartmentRoleSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = ["id", "name", "roles"]

    def get_roles(self, dept):
        user = self.context["user"]
        roles = UserRole.objects.filter(user=user, department=dept)
        return [
            {
                "role_id": r.role.id,
                "role_name": r.role.name,
                "permissions": [
                    rp.permission.code for rp in r.role.role_permissions.all()
                ]
            }
            for r in roles
        ]


class UserMeSerializer(serializers.ModelSerializer):
    departments = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "departments"]

    def get_departments(self, user):
        user_depts = {ur.department for ur in user.user_roles.all()}
        return UserDepartmentRoleSerializer(user_depts, many=True, context={"user": user}).data
