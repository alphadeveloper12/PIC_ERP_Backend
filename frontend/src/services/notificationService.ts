import api from './api';

export interface Notification {
    id: number;
    title: string;
    message: string;
    notification_type: 'OVERDUE' | 'UNASSIGNED' | 'PROJECT_STATUS' | 'GENERAL';
    is_read: boolean;
    created_at: string;
    related_task?: number;
    related_project?: number;
}

export const notificationService = {
    getAll: async () => {
        const response = await api.get<Notification[]>('/dms/notifications/');
        return response.data;
    },

    markRead: async (id: number) => {
        const response = await api.post(`/dms/notifications/${id}/mark_read/`);
        return response.data;
    },

    markAllRead: async () => {
        const response = await api.post('/dms/notifications/mark_all_read/');
        return response.data;
    }
};
