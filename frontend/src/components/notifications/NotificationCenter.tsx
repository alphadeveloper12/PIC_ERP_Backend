import { useState, useEffect, useRef } from 'react';
import { Bell, Check, Clock, AlertTriangle, Info, Calendar, ShieldAlert, ArrowRight, CheckSquare } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { notificationService, type Notification } from '@/services/notificationService';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '@/hooks/useAuthStore';

export function NotificationCenter() {
    const [isOpen, setIsOpen] = useState(false);
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [unreadCount, setUnreadCount] = useState(0);
    const containerRef = useRef<HTMLDivElement>(null);
    const navigate = useNavigate();
    const { user } = useAuthStore();

    const fetchNotifications = async () => {
        try {
            const data = await notificationService.getAll();
            setNotifications(data.slice(0, 10)); // Only show last 10 in dropdown
            setUnreadCount(data.filter(n => !n.is_read).length);
        } catch (error) {
            console.error("Failed to fetch notifications", error);
        }
    };

    useEffect(() => {
        if (user?.id) {
            fetchNotifications();
            const interval = setInterval(fetchNotifications, 60000);
            return () => clearInterval(interval);
        }
    }, [user?.id]);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const handleMarkRead = async (id: number) => {
        try {
            await notificationService.markRead(id);
            setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
            setUnreadCount(prev => Math.max(0, prev - 1));
        } catch (error) {
            console.error(error);
        }
    };

    const handleMarkAllRead = async () => {
        try {
            await notificationService.markAllRead();
            setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
            setUnreadCount(0);
        } catch (error) {
            console.error(error);
        }
    };

    const getIcon = (type: string, isRead: boolean) => {
        switch (type) {
            case 'OVERDUE': return <ShieldAlert className={cn("h-4 w-4 text-red-500", !isRead && "animate-pulse")} />;
            case 'UNASSIGNED': return <Info className="h-4 w-4 text-blue-500" />;
            case 'PROJECT_STATUS': return <Calendar className="h-4 w-4 text-amber-500" />;
            default: return <Bell className="h-4 w-4 text-slate-400" />;
        }
    };

    return (
        <div className="relative" ref={containerRef}>
            <Button
                variant="ghost"
                size="icon"
                className={cn(
                    "relative h-12 w-12 rounded-xl transition-all duration-300",
                    isOpen ? "bg-primary/5 text-primary" : "hover:bg-slate-100"
                )}
                onClick={() => setIsOpen(!isOpen)}
            >
                <Bell className={cn("h-5 w-5")} />
                {unreadCount > 0 && (
                    <>
                        <span className="absolute top-3 right-3 h-2.5 w-2.5 rounded-full bg-primary ring-2 ring-background z-10" />
                        <span className="absolute top-3 right-3 h-2.5 w-2.5 rounded-full bg-primary animate-ping opacity-75" />
                    </>
                )}
            </Button>

            {isOpen && (
                <div className="absolute right-0 mt-4 w-80 sm:w-96 erp-card bg-card border shadow-2xl z-[60] overflow-hidden animate-in fade-in slide-in-from-top-2 duration-300 ring-1 ring-primary/5">
                    <div className="flex items-center justify-between p-6 bg-slate-50/50 border-b border-primary/5">
                        <div className="space-y-0.5">
                            <h4 className="text-sm font-black uppercase tracking-widest text-foreground">Intelligence</h4>
                            {unreadCount > 0 && <p className="text-[10px] font-bold text-primary italic">{unreadCount} active alerts requiring attention</p>}
                        </div>
                        {unreadCount > 0 && (
                            <Button variant="ghost" size="sm" className="h-8 px-3 rounded-lg text-[10px] font-black uppercase tracking-widest text-muted-foreground hover:text-primary hover:bg-primary/5" onClick={handleMarkAllRead}>
                                Reset All
                            </Button>
                        )}
                    </div>

                    <div className="max-h-[360px] overflow-y-auto no-scrollbar">
                        {notifications.length === 0 ? (
                            <div className="p-12 text-center space-y-3">
                                <div className="h-12 w-12 bg-slate-50 rounded-2xl flex items-center justify-center mx-auto text-slate-300">
                                    <Bell className="h-6 w-6" />
                                </div>
                                <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground/40">Workspace Clear</p>
                            </div>
                        ) : (
                            <div className="divide-y divide-primary/5">
                                {notifications.map((n) => (
                                    <div
                                        key={n.id}
                                        className={cn(
                                            "flex items-start gap-4 p-5 hover:bg-slate-50 cursor-pointer transition-all duration-300 group relative text-left",
                                            !n.is_read ? "bg-primary/[0.02]" : "bg-card"
                                        )}
                                        onClick={() => {
                                            if (!n.is_read) handleMarkRead(n.id);
                                            setIsOpen(false);
                                            if (n.related_task) navigate(`/dms/tasks/${n.related_task}`);
                                        }}
                                    >
                                        <div className="mt-1 shrink-0">
                                            {getIcon(n.notification_type, n.is_read)}
                                        </div>
                                        <div className="flex-1 space-y-1.5 min-w-0">
                                            <div className="flex justify-between items-start gap-2">
                                                <p className={cn("text-xs leading-tight tracking-tight", !n.is_read ? "font-black text-foreground" : "font-bold text-muted-foreground")}>
                                                    {n.title}
                                                </p>
                                                <span className="text-[9px] font-black text-muted-foreground/30 whitespace-nowrap">
                                                    {new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                </span>
                                            </div>
                                            <p className="text-[11px] font-bold text-muted-foreground/60 line-clamp-1 italic group-hover:line-clamp-none transition-all">
                                                {n.message}
                                            </p>
                                        </div>

                                        {!n.is_read && (
                                            <div
                                                className="absolute right-4 bottom-4 h-6 w-6 rounded-lg bg-card border shadow-sm flex items-center justify-center opacity-0 group-hover:opacity-100 hover:text-primary transition-all scale-75 group-hover:scale-100"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleMarkRead(n.id);
                                                }}
                                            >
                                                <CheckSquare className="h-3 w-3" />
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    <div className="p-4 bg-slate-50/80 border-t border-primary/5">
                        <Link to="/notifications" onClick={() => setIsOpen(false)}>
                            <Button variant="ghost" className="w-full h-10 rounded-xl text-[10px] font-black uppercase tracking-[0.2em] text-primary hover:bg-primary/5">
                                Full Registry <ArrowRight className="ml-2 h-3 w-3" />
                            </Button>
                        </Link>
                    </div>
                </div>
            )}
        </div>
    );
}
