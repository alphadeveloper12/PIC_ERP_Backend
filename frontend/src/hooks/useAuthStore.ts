import { create } from 'zustand';
import api from '@/services/api';

interface User {
    id: number;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    is_superuser: boolean;
    is_owner: boolean;
    owned_project_ids: number[];
    is_hod?: boolean;
    department_roles?: Array<{
        project_id: number;
        project_name: string;
        department_code: string;
        department_name: string;
        role: string;
        permissions: string[];
    }>;
    permissions?: string[];
    project_permissions?: Record<string, string[]>;
}

interface AuthState {
    user: User | null;
    token: string | null;
    login: (credentials: any) => Promise<void>;
    logout: () => void;
    register: (data: any) => Promise<void>;
    verifySession: () => Promise<boolean>;
}

export const useAuthStore = create<AuthState>((set) => ({
    user: JSON.parse(localStorage.getItem('user') || 'null'),
    token: localStorage.getItem('token'),
    login: async (credentials) => {
        try {
            // Adjusted endpoint to match backend:
            const response = await api.post('/api/auth/login/', credentials);
            const { token, refresh, user } = response.data;

            localStorage.setItem('token', token);
            localStorage.setItem('refresh', refresh);
            localStorage.setItem('user', JSON.stringify(user));

            set({ token, user });
        } catch (error) {
            console.error('Login failed', error);
            throw error;
        }
    },
    logout: () => {
        localStorage.removeItem('token');
        localStorage.removeItem('refresh');
        localStorage.removeItem('user');
        set({ user: null, token: null });
    },
    register: async (data) => {
        await api.post('/api/auth/register/', data);
    },
    verifySession: async () => {
        try {
            const response = await api.get('/api/auth/me/');
            // Update user data if needed, or just confirm it's valid
            const { user } = response.data;
            set({ user });
            localStorage.setItem('user', JSON.stringify(user));
            return true;
        } catch (error) {
            set({ token: null, user: null });
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            return false;
        }
    }
}));
