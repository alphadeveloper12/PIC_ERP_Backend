import { useState, useEffect, useMemo } from 'react';
import { Button } from "@/components/ui/button";
import { notificationService, type Notification } from "@/services/notificationService";
import { Bell, Info, Calendar, CheckSquare, Trash2, ShieldAlert, Sparkles } from 'lucide-react';
import { cn } from "@/lib/utils";
import { useNavigate } from "react-router-dom";

type FilterTab = 'all' | 'unread' | 'critical' | 'system';

export function NotificationsPage() {
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [activeTab, setActiveTab] = useState<FilterTab>('all');
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    const fetchNotifications = async () => {
        setLoading(true);
        try {
            const data = await notificationService.getAll();
            setNotifications(data);
        } catch (error) {
            console.error("Failed to fetch notifications", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchNotifications();
    }, []);

    const handleMarkRead = async (id: number) => {
        try {
            await notificationService.markRead(id);
            setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
        } catch (error) {
            console.error(error);
        }
    };

    const handleMarkAllRead = async () => {
        try {
            await notificationService.markAllRead();
            setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
        } catch (error) {
            console.error(error);
        }
    };

    const filteredNotifications = useMemo(() => {
        return notifications.filter(n => {
            if (activeTab === 'unread') return !n.is_read;
            if (activeTab === 'critical') return n.notification_type === 'OVERDUE';
            if (activeTab === 'system') return n.notification_type === 'PROJECT_STATUS' || n.notification_type === 'UNASSIGNED';
            return true;
        });
    }, [notifications, activeTab]);

    const groupedNotifications = useMemo(() => {
        const now = new Date();
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);

        const groups: Record<string, Notification[]> = {
            'Today': [],
            'Yesterday': [],
            'Older': []
        };

        filteredNotifications.forEach(n => {
            const date = new Date(n.created_at);
            if (date >= today) groups['Today'].push(n);
            else if (date >= yesterday) groups['Yesterday'].push(n);
            else groups['Older'].push(n);
        });

        return groups;
    }, [filteredNotifications]);

    const getIcon = (type: string, isRead: boolean) => {
        const baseClass = "h-5 w-5";
        switch (type) {
            case 'OVERDUE':
                return <div className={cn("p-2 rounded-xl bg-red-100/50 text-red-600 shadow-sm", !isRead && "animate-pulse")}>
                    <ShieldAlert className={baseClass} />
                </div>;
            case 'UNASSIGNED':
                return <div className="p-2 rounded-xl bg-blue-100/50 text-blue-600 shadow-sm">
                    <Info className={baseClass} />
                </div>;
            case 'PROJECT_STATUS':
                return <div className="p-2 rounded-xl bg-amber-100/50 text-amber-600 shadow-sm">
                    <Calendar className={baseClass} />
                </div>;
            default:
                return <div className="p-2 rounded-xl bg-slate-100/50 text-slate-600 shadow-sm">
                    <Bell className={baseClass} />
                </div>;
        }
    };

    return (
        <div className="space-y-8 animate-in fade-in duration-500 max-w-6xl mx-auto">
            <header className="erp-header flex flex-col xl:flex-row justify-between items-start xl:items-center gap-8">
                <div className="space-y-1">
                    <h1 className="text-2xl font-black tracking-tight text-foreground flex items-center gap-3">
                        Intelligence Center
                        {notifications.filter(n => !n.is_read).length > 0 && (
                            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary text-[10px] text-white">
                                {notifications.filter(n => !n.is_read).length}
                            </span>
                        )}
                    </h1>
                    <p className="text-sm font-bold text-muted-foreground italic">Unified activity stream and system intelligence alerts.</p>
                </div>

                <div className="flex flex-col sm:flex-row gap-4 w-full xl:w-auto">
                    <div className="flex bg-muted/20 p-1.5 rounded-2xl erp-glass border border-primary/5">
                        {(['all', 'unread', 'critical'] as const).map((tab) => (
                            <button
                                key={tab}
                                onClick={() => setActiveTab(tab)}
                                className={cn(
                                    "px-6 py-2.5 text-[10px] font-black uppercase tracking-[0.15em] rounded-xl transition-all",
                                    activeTab === tab ? "bg-card shadow-xl text-primary scale-100" : "text-muted-foreground/40 hover:text-muted-foreground/80"
                                )}
                            >
                                {tab}
                            </button>
                        ))}
                    </div>
                    <Button
                        variant="outline"
                        onClick={handleMarkAllRead}
                        className="h-12 px-6 rounded-2xl border-2 font-black text-[10px] uppercase tracking-widest hover:bg-slate-50 transition-all border-slate-100"
                        disabled={!notifications.some(n => !n.is_read)}
                    >
                        Mark All Read
                    </Button>
                </div>
            </header>

            <div className="space-y-12">
                {Object.entries(groupedNotifications).map(([label, list]) => (
                    list.length > 0 && (
                        <section key={label} className="space-y-6">
                            <div className="flex items-center gap-4 px-2">
                                <h3 className="text-[10px] font-black uppercase tracking-[0.3em] text-muted-foreground/40">{label}</h3>
                                <div className="h-px flex-1 bg-muted/30" />
                            </div>

                            <div className="grid gap-4">
                                {list.map((n) => (
                                    <div
                                        key={n.id}
                                        className={cn(
                                            "erp-card bg-card border group hover:scale-[1.01] transition-all duration-300 relative overflow-hidden",
                                            !n.is_read ? "border-primary/20 bg-primary/5 ring-1 ring-primary/5" : "border-transparent"
                                        )}
                                    >
                                        <div className="p-6 sm:p-8 flex gap-6 items-start">
                                            <div className="shrink-0 pt-1">
                                                {getIcon(n.notification_type, n.is_read)}
                                            </div>

                                            <div
                                                className="flex-1 min-w-0 cursor-pointer text-left"
                                                onClick={() => {
                                                    if (!n.is_read) handleMarkRead(n.id);
                                                    if (n.related_task) navigate(`/dms/tasks/${n.related_task}`);
                                                    else if (n.related_project) navigate('/');
                                                }}
                                            >
                                                <div className="flex justify-between items-start gap-4">
                                                    <h4 className={cn("text-lg font-black tracking-tight leading-snug", !n.is_read ? "text-primary" : "text-foreground/80")}>
                                                        {n.title}
                                                    </h4>
                                                    <span className="text-[10px] font-black text-muted-foreground/40 uppercase tracking-widest whitespace-nowrap pt-1">
                                                        {new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                    </span>
                                                </div>
                                                <p className="mt-2 text-sm font-bold text-muted-foreground leading-relaxed italic max-w-3xl">
                                                    {n.message}
                                                </p>

                                                <div className="mt-6 flex items-center gap-4">
                                                    <span className="text-[9px] font-black uppercase tracking-[0.2em] bg-slate-100 dark:bg-slate-800 px-3 py-1 rounded-lg text-slate-500">
                                                        {n.notification_type.replace('_', ' ')}
                                                    </span>
                                                    {!n.is_read && (
                                                        <span className="flex items-center gap-1.5 text-[9px] font-black uppercase tracking-[0.2em] text-primary">
                                                            <div className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse" />
                                                            Action Required
                                                        </span>
                                                    )}
                                                </div>
                                            </div>

                                            <div className="flex flex-col gap-2">
                                                {!n.is_read && (
                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        onClick={() => handleMarkRead(n.id)}
                                                        className="h-10 w-10 rounded-xl hover:bg-primary/10 hover:text-primary"
                                                        title="Mark as read"
                                                    >
                                                        <CheckSquare className="h-4 w-4" />
                                                    </Button>
                                                )}
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    className="h-10 w-10 rounded-xl hover:bg-destructive/10 hover:text-destructive text-muted-foreground/30 transition-all opacity-0 group-hover:opacity-100"
                                                    title="Delete"
                                                >
                                                    <Trash2 className="h-4 w-4" />
                                                </Button>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </section>
                    )
                ))}

                {!loading && filteredNotifications.length === 0 && (
                    <div className="erp-card bg-muted/5 border-2 border-dashed border-muted/20 p-24 text-center">
                        <div className="h-24 w-24 bg-white rounded-[2rem] flex items-center justify-center mx-auto mb-8 shadow-xl shadow-primary/5">
                            <Sparkles className="h-12 w-12 text-primary/20" />
                        </div>
                        <h3 className="text-2xl font-black text-foreground">Nothing to report</h3>
                        <p className="text-sm font-bold text-muted-foreground mt-2 italic">You're all caught up with current system activity.</p>
                        <Button
                            variant="ghost"
                            className="mt-8 font-black text-[10px] uppercase tracking-widest text-primary"
                            onClick={() => setActiveTab('all')}
                        >
                            View Historical Log
                        </Button>
                    </div>
                )}
            </div>
        </div>
    );
}
