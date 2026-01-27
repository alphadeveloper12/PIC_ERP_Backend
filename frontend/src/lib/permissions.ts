import { useAuthStore } from "@/hooks/useAuthStore";

/**
 * Hook or function to check if the logged in user has a specific permission.
 */
export const usePermissions = () => {
    const user = useAuthStore((state) => state.user);

    const hasPermission = (permissionCode: string, projectId?: number) => {
        if (!user) return false;
        if (user.is_superuser) return true;

        // If it's a project owner checking a project they own, grant all
        if (projectId && user.owned_project_ids?.includes(projectId)) {
            return true;
        }

        // NEW: Check project-specific permissions first
        if (projectId && user.project_permissions && user.project_permissions[projectId]) {
            // If we have explicit permissions for this project, rely ONLY on them.
            // This prevents "bleed over" from other projects.
            return user.project_permissions[projectId].includes(permissionCode);
        }

        // Fallback (Legacy): Check flat list if no project context is given OR if project_permissions missing
        // However, if projectId IS given but missing from project_permissions, it means NO access for that project.
        if (projectId) {
            // If we are checking for a specific project, and we didn't match above:
            // 1. User doesn't own it.
            // 2. User has no specific roles in it (project_permissions[projectId] is undefined).
            // strictly return false.
            return false;
        }

        return user.permissions?.includes(permissionCode) || false;
    };

    const hasAnyPermission = (permissionCodes: string[], projectId?: number) => {
        if (!user) return false;
        if (user.is_superuser) return true;

        if (projectId && user.owned_project_ids?.includes(projectId)) {
            return true;
        }

        if (projectId && user.project_permissions && user.project_permissions[projectId]) {
            const projectPerms = user.project_permissions[projectId];
            return permissionCodes.some(code => projectPerms.includes(code));
        }

        if (projectId) {
            return false;
        }

        return permissionCodes.some(code => user.permissions?.includes(code));
    };

    return { hasPermission, hasAnyPermission };
};
