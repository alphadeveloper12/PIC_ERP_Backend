from rest_framework.permissions import BasePermission

class RolePermission(BasePermission):
    """
    Very simple role check via header:
    - viewer: read-only (GET)
    - editor: full access (POST/PUT/PATCH/DELETE)
    Set request header: X-ROLE: editor | viewer
    """
    def has_permission(self, request, view):
        role = request.headers.get("X-ROLE", "viewer").lower()
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        # write operations:
        return role == "editor"
