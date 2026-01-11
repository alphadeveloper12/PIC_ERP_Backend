import { create } from 'zustand';
import api from '@/services/api';

interface User {
    id: number;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    is_superuser: boolean;
    is_owner?: boolean;
    is_hod?: boolean;
}

interface AuthState {
    user: User | null;
    token: string | null;
    login: (credentials: any) => Promise<void>;
    logout: () => void;
    register: (data: any) => Promise<void>;
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
    }
}));
