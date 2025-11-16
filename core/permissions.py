from rest_framework.permissions import BasePermission

class HasERPAccess(BasePermission):

    def has_permission(self, request, view):
        user = request.user
        required_perm = getattr(view, "required_permission", None)

        if not required_perm:
            return True  # no specific permission required

        # collect permissions from all roles
        user_perms = set()
        for ur in user.user_roles.all():
            for rp in ur.role.role_permissions.all():
                user_perms.add(rp.permission.code)

        return required_perm in user_perms
