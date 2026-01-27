import { useState } from "react";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuthStore } from "@/hooks/useAuthStore";
import { cn } from "@/lib/utils";
import {
    LogOut,
    LayoutDashboard,
    Users,
    FolderOpen,
    FileText,
    Menu,
    ShieldCheck,
    CalendarDays,
    ChevronLeft,
    ChevronRight
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Toaster } from "sonner";
import { usePermissions } from "@/lib/permissions";
import { NotificationCenter } from "@/components/notifications/NotificationCenter";

interface SidebarItemProps {
    icon: React.ElementType;
    label: string;
    href: string;
    active?: boolean;
    isCollapsed?: boolean;
}

function SidebarItem({ icon: Icon, label, href, active, isCollapsed }: SidebarItemProps) {
    return (
        <Link
            to={href}
            title={isCollapsed ? label : undefined}
            className={cn(
                "flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-bold transition-all duration-200 uppercase tracking-widest",
                active
                    ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20 scale-[1.02]"
                    : "text-slate-400 hover:text-white hover:bg-white/5",
                isCollapsed && "justify-center px-0"
            )}
        >
            <Icon className={cn("h-4 w-4 shrink-0", active ? "text-white" : "text-slate-500")} />
            {!isCollapsed && label}
        </Link>
    );
}

export function Layout() {
    const { logout, user } = useAuthStore();
    const { hasAnyPermission } = usePermissions();
    const location = useLocation();
    const navigate = useNavigate();
    const [isMobileOpen, setIsMobileOpen] = useState(false);
    const [isCollapsed, setIsCollapsed] = useState(false);

    const handleLogout = () => {
        logout();
        navigate("/login");
    };

    // Filter navigation items based on user permissions
    const allNavItems = [
        { icon: LayoutDashboard, label: "Dashboard", href: "/" },
        {
            icon: FileText,
            label: "Tasks",
            href: "/dms",
            requiredPermission: ['approve_tasks', 'submit_tasks', 'view_tasks']
        },
        {
            icon: Users,
            label: "Team",
            href: "/team",
            requiredPermission: ['manage_team', 'view_team', 'manage_project_owner']
        },
        {
            icon: CalendarDays,
            label: "Planning",
            href: "/planning",
            requiredPermission: ['manage_planning', 'view_planning']
        },
        {
            icon: FolderOpen,
            label: "Projects",
            href: "/projects",
            requiredPermission: ['manage_projects']
        },
        {
            icon: Users,
            label: "Users (Admin)",
            href: "/users",
            requiredPermission: ['manage_users', 'superuser']
        },
        {
            icon: ShieldCheck,
            label: "Permissions",
            href: "/permissions",
            requiredPermission: ['manage_projects']
        }
    ];

    const navItems = allNavItems.filter(item => {
        if (!item.requiredPermission) return true;

        // Superusers see all sidebar items
        if (user?.is_superuser) return true;

        // Project Owners specifics
        if (user?.is_owner) {
            if (item.href === '/users' || item.href === '/projects') return false;
            return true;
        }

        return hasAnyPermission(item.requiredPermission);
    });

    return (
        <div className={cn(
            "grid h-screen w-full bg-background overflow-hidden transition-all duration-300 ease-in-out",
            isCollapsed ? "md:grid-cols-[80px_1fr]" : "md:grid-cols-[240px_1fr] lg:grid-cols-[300px_1fr]"
        )}>
            {/* Sidebar */}
            <div className="hidden border-r border-white/5 bg-slate-950 md:block overflow-hidden relative">
                {/* Decorative element */}
                <div className="absolute top-0 right-0 w-32 h-32 bg-primary/10 rounded-full -translate-y-1/2 translate-x-1/2 blur-2xl" />

                <div className="flex h-full max-h-screen flex-col gap-6 relative z-10">
                    <div className="flex h-20 items-center justify-between border-b border-white/5 px-4">
                        <Link to="/" className={cn("flex items-center gap-3", isCollapsed && "justify-center w-full")}>
                            <div className="bg-primary p-2 rounded-xl shadow-lg shadow-primary/20 shrink-0">
                                <ShieldCheck className="h-6 w-6 text-white" />
                            </div>
                            {!isCollapsed && <span className="font-black text-xl tracking-tighter text-white">PIC <span className="text-primary">ERP</span></span>}
                        </Link>
                    </div>
                    <div className="flex-1 px-4 overflow-y-auto no-scrollbar">
                        <nav className="flex flex-col gap-2">
                            {!isCollapsed && <p className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-500 mb-2 px-4">Main Menu</p>}
                            {navItems.map((item) => (
                                <SidebarItem
                                    key={item.href}
                                    icon={item.icon}
                                    label={item.label}
                                    href={item.href}
                                    active={location.pathname === item.href}
                                    isCollapsed={isCollapsed}
                                />
                            ))}
                        </nav>
                    </div>

                    {/* User Info Section */}
                    <div className={cn("mt-auto border-t border-white/5 bg-white/5 backdrop-blur-md transition-all", isCollapsed ? "p-4" : "p-6")}>
                        {!isCollapsed && (
                            <div className="mb-6 flex flex-col gap-1.5 px-1 text-center sm:text-left">
                                <p className="text-sm font-black text-white">{user?.first_name} {user?.last_name}</p>
                                <p className="text-xs font-bold text-slate-500 italic">@{user?.username}</p>
                                <div className="mt-3 inline-block self-start px-3 py-1 bg-primary/10 rounded-full text-[9px] font-black uppercase tracking-widest text-primary border border-primary/20">
                                    {user?.is_superuser ? "System Global Admin" :
                                        user?.is_owner ? "Project Owner" : "Officer / Staff"}
                                </div>
                            </div>
                        )}
                        <Button
                            variant="ghost"
                            size="sm"
                            className={cn(
                                "w-full justify-center gap-3 h-12 rounded-xl font-black text-xs uppercase tracking-widest text-slate-400 hover:text-white hover:bg-destructive/10 hover:text-red-400 transition-all border border-transparent hover:border-red-500/20",
                                isCollapsed && "px-0"
                            )}
                            onClick={handleLogout}
                            title={isCollapsed ? "Logoff" : undefined}
                        >
                            <LogOut className="h-4 w-4 shrink-0" />
                            {!isCollapsed && "Logoff"}
                        </Button>
                    </div>
                </div>
            </div>

            {/* Main Content Area */}
            <div className="flex flex-col h-full overflow-hidden">
                <header className="flex h-20 items-center gap-4 bg-white/80 backdrop-blur-md px-6 lg:px-10 border-b border-slate-100 flex-shrink-0 sticky top-0 z-50">
                    <Button
                        variant="outline"
                        size="icon"
                        className="shrink-0 md:hidden rounded-xl border-2"
                        onClick={() => setIsMobileOpen(!isMobileOpen)}
                    >
                        <Menu className="h-5 w-5" />
                        <span className="sr-only">Toggle navigation menu</span>
                    </Button>
                    <Button
                        variant="ghost"
                        size="icon"
                        className="hidden md:flex shrink-0 rounded-xl hover:bg-slate-100"
                        onClick={() => setIsCollapsed(!isCollapsed)}
                    >
                        {isCollapsed ? <ChevronRight className="h-5 w-5" /> : <ChevronLeft className="h-5 w-5" />}
                    </Button>
                    <div className="w-full flex-1 md:hidden">
                        <span className="font-black tracking-tighter text-xl text-foreground">PIC <span className="text-primary">ERP</span></span>
                    </div>
                    <div className="ml-auto flex items-center gap-4">
                        <NotificationCenter />
                    </div>
                </header>

                <main className="flex-1 overflow-y-auto bg-slate-50/50">
                    <div className="container mx-auto py-8 px-6 lg:py-12 lg:px-10 max-w-[1600px]">
                        <Outlet />
                    </div>
                </main>
            </div>
            <Toaster position="top-right" richColors />
        </div>
    );
}

