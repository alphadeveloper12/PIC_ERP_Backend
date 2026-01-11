import { useState } from "react";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuthStore } from "@/hooks/useAuthStore";
import { cn } from "@/lib/utils";
import {
    LogOut,
    LayoutDashboard,
    Users,
    Settings,
    FolderOpen,
    FileText,
    Menu,
    Upload,
    Database,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Toaster } from "sonner";

interface SidebarItemProps {
    icon: React.ElementType;
    label: string;
    href: string;
    active?: boolean;
}

function SidebarItem({ icon: Icon, label, href, active }: SidebarItemProps) {
    return (
        <Link
            to={href}
            className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground transition-all hover:text-primary",
                active && "bg-muted text-primary"
            )}
        >
            <Icon className="h-4 w-4" />
            {label}
        </Link>
    );
}

export function Layout() {
    const { logout, user } = useAuthStore();
    const location = useLocation();
    const navigate = useNavigate();
    const [isMobileOpen, setIsMobileOpen] = useState(false);

    const handleLogout = () => {
        logout();
        navigate("/login");
    };

    // Determine navigation items based on generic role or just show all for demo
    // In a real app, filter based on user.role
    // Filter navigation items based on user role
    const navItems = [
        { icon: LayoutDashboard, label: "Dashboard", href: "/" },
        { icon: FileText, label: "Tasks", href: "/dms" },
        { icon: Users, label: "Team", href: "/team" },
        { icon: Upload, label: "Upload P6", href: "/planning/upload" },
        { icon: Database, label: "P6 Activities", href: "/planning/activities" },
    ];

    // Admin-only items
    if (user?.is_superuser) {
        navItems.push(
            { icon: FolderOpen, label: "Projects", href: "/projects" },
            { icon: Users, label: "Users (Admin)", href: "/users" }
        );
    }

    return (
        <div className="grid min-h-screen w-full md:grid-cols-[220px_1fr] lg:grid-cols-[280px_1fr]">
            <div className="hidden border-r bg-muted/40 md:block">
                <div className="flex h-full max-h-screen flex-col gap-2">
                    <div className="flex h-14 items-center border-b px-4 lg:h-[60px] lg:px-6">
                        <Link to="/" className="flex items-center gap-2 font-semibold">
                            <span className="">PIC ERP</span>
                        </Link>
                    </div>
                    <div className="flex-1">
                        <nav className="grid items-start px-2 text-sm font-medium lg:px-4">
                            {navItems.map((item) => (
                                <SidebarItem
                                    key={item.href}
                                    icon={item.icon}
                                    label={item.label}
                                    href={item.href}
                                    active={location.pathname === item.href}
                                />
                            ))}
                        </nav>
                    </div>

                    {/* User Info Section */}
                    <div className="mt-auto border-t p-4">
                        <div className="mb-4 flex flex-col gap-1 px-2">
                            <p className="text-sm font-medium leading-none text-foreground">{user?.first_name} {user?.last_name}</p>
                            <p className="text-xs leading-none text-muted-foreground">@{user?.username}</p>
                            <div className="mt-2 text-[10px] font-bold uppercase tracking-wider text-primary/70">
                                {user?.is_superuser ? "System Administrator" :
                                    user?.is_owner ? "Project Owner" : "Team Member"}
                            </div>
                        </div>
                        <Button
                            variant="outline"
                            size="sm"
                            className="w-full justify-start gap-2"
                            onClick={handleLogout}
                        >
                            <LogOut className="h-4 w-4" />
                            Logout
                        </Button>
                    </div>
                </div>
            </div>
            <div className="flex flex-col">
                <header className="flex h-14 items-center gap-4 border-b bg-muted/40 px-4 lg:h-[60px] lg:px-6 md:hidden">
                    <Button
                        variant="outline"
                        size="icon"
                        className="shrink-0"
                        onClick={() => setIsMobileOpen(!isMobileOpen)}
                    >
                        <Menu className="h-5 w-5" />
                        <span className="sr-only">Toggle navigation menu</span>
                    </Button>
                    <div className="w-full flex-1">
                        <span className="font-semibold">PIC ERP</span>
                    </div>
                </header>
                <main className="flex flex-1 flex-col gap-4 p-4 lg:gap-6 lg:p-6 bg-muted/10">
                    <Outlet />
                </main>
            </div>
            <Toaster position="top-right" richColors />
        </div>
    );
}
