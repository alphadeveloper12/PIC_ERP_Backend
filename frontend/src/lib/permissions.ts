import { useAuthStore } from "@/hooks/useAuthStore";

/**
 * Hook or function to check if the logged in user has a specific permission.
 */
export const usePermissions = () => {
    const user = useAuthStore((state) => state.user);

    const hasPermission = (permissionCode: string, projectId?: number) => {
        if (user?.is_superuser) return true;

        // If it's a project owner checking a project they own, grant all
        if (projectId && user?.owned_project_ids?.includes(projectId)) {
            return true;
        }

        return user?.permissions?.includes(permissionCode) || false;
    };

    const hasAnyPermission = (permissionCodes: string[], projectId?: number) => {
        if (user?.is_superuser) return true;

        if (projectId && user?.owned_project_ids?.includes(projectId)) {
            return true;
        }

        return permissionCodes.some(code => user?.permissions?.includes(code));
    };

    return { hasPermission, hasAnyPermission };
};
