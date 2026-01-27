import { useState, useEffect } from 'react';
import api from '@/services/api';
import { useAuthStore } from '@/hooks/useAuthStore';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { AlertCircle, ArrowRight, CheckCircle, ClipboardList, Clock, Users, FileText, PlayCircle, Loader2 } from 'lucide-react';
import { Loading } from '@/components/Loading';
import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';
import { ProjectHealthWidget, type HealthData } from '@/components/dashboard/ProjectHealthWidget';
import { cn } from '@/lib/utils';

interface DashboardStats {
    total: number;
    pending: number;
    assigned: number;
    in_progress: number;
    submitted: number;
    approved: number;
    rejected: number;
}

interface Task {
    id: number;
    status: string;
    project_name: string;
    p6_activity_name?: string;
    workflow_step_details?: {
        sequence_id: string;
        action_description: string;
    };
    comments: string;
}

export default function Dashboard() {
    const { user } = useAuthStore();
    const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [pendingTasks, setPendingTasks] = useState<Task[]>([]);
    const [projects, setProjects] = useState<any[]>([]);
    const [healthSummary, setHealthSummary] = useState<Record<number, HealthData>>({});
    const [loading, setLoading] = useState(true);

    const getMode = () => {
        if (user?.is_superuser) return 'all_tasks';
        if (user?.is_owner) return 'project_owner';
        if (user?.is_hod) return 'department';
        return 'my_tasks';
    };

    const fetchDashboardData = async () => {
        setLoading(true);
        const mode = getMode();
        const projectParam = selectedProjectId ? `&project_id=${selectedProjectId}` : '';

        try {
            const [statsRes, tasksRes, projRes] = await Promise.all([
                api.get(`/dms/tasks/dashboard_stats/?mode=${mode}${projectParam}`),
                api.get(`/dms/tasks/?mode=${mode}&status=${mode === 'department' ? 'PENDING' : 'SUBMITTED'}${projectParam}`),
                api.get('/api/projects/')
            ]);

            let healthData = {};
            try {
                const healthRes = await api.get('/api/projects/health_summary/');
                healthData = healthRes.data.data || {};
            } catch (err) {
                console.warn("Failed to load health summary", err);
            }

            setStats(statsRes.data);
            setPendingTasks(tasksRes.data.results || tasksRes.data);
            setProjects(projRes.data.data || []);
            setHealthSummary(healthData);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (user?.id) fetchDashboardData();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [user?.id, selectedProjectId]);

    if (!user) return null;

    const StatCard = ({ title, value, icon: Icon, color, subText }: any) => (
        <Card className="erp-card bg-card overflow-hidden group hover:shadow-primary/10 flex flex-col h-full ring-1 ring-primary/5">
            <div className={`h-1.5 w-full ${color} opacity-80`} />
            <CardContent className="pt-6 flex-1 flex flex-col justify-center">
                <div className="flex items-center justify-between gap-4">
                    <div className="min-w-0 flex-1 text-left">
                        <p className="text-[10px] sm:text-xs font-black uppercase tracking-[0.15em] text-muted-foreground/60 truncate">{title}</p>
                        <div className="flex items-baseline gap-2 mt-1.5">
                            <p className="text-2xl sm:text-3xl font-black tracking-tighter text-foreground">{value}</p>
                            {subText && <span className="text-[10px] sm:text-xs text-muted-foreground/50 font-bold truncate italic">{subText}</span>}
                        </div>
                    </div>
                    <div className={`p-2.5 sm:p-3 rounded-2xl bg-opacity-10 ${color.replace('bg-', 'text-')} bg-current group-hover:scale-110 transition-transform shrink-0`}>
                        <Icon className="h-5 w-5 sm:h-6 sm:w-6" />
                    </div>
                </div>
            </CardContent>
        </Card>
    );

    const filteredProjects = selectedProjectId
        ? projects.filter(p => p.id === selectedProjectId)
        : projects.filter(p => healthSummary[p.id]);

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            <header className="erp-header flex flex-col xl:flex-row justify-between items-start xl:items-center gap-6">
                <div className="space-y-1 text-left">
                    <h1 className="text-2xl font-black tracking-tight text-foreground">
                        Hello, {user.first_name}
                    </h1>
                    <p className="text-base sm:text-lg font-bold text-muted-foreground italic">
                        {user.is_superuser ? 'System Intelligence Center' :
                            user.is_owner ? 'Project Command Deck' :
                                user.is_hod ? 'Departmental Control' : 'Workspace Overview'}
                    </p>
                </div>

                <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 w-full xl:w-auto">
                    <div className="relative group flex-1 sm:min-w-[280px]">
                        <select
                            className="w-full h-12 pl-4 pr-10 bg-slate-50 border-2 border-slate-100 focus:border-primary/20 rounded-2xl font-black text-sm appearance-none cursor-pointer transition-all outline-none"
                            value={selectedProjectId || ''}
                            onChange={e => setSelectedProjectId(e.target.value ? Number(e.target.value) : null)}
                        >
                            <option value="">🌎 Global Overview</option>
                            {projects.map(prj => (
                                <option key={prj.id} value={prj.id}>[{prj.code}] {prj.name}</option>
                            ))}
                        </select>
                        <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-primary/40 group-hover:text-primary transition-colors">
                            <ArrowRight className="h-4 w-4 rotate-90" />
                        </div>
                    </div>

                    <div className="flex gap-2">
                        <Button variant="outline" onClick={fetchDashboardData} className="flex-1 sm:flex-none rounded-2xl h-12 px-6 font-black text-xs border-2 transition-all hover:bg-slate-50" disabled={loading}>
                            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Refresh'}
                        </Button>
                        <Link to="/dms" className="flex-1 sm:flex-none">
                            <Button className="w-full rounded-2xl h-12 px-8 font-black text-xs shadow-xl shadow-primary/20 transition-all hover:scale-[1.02]">DMS Tasks</Button>
                        </Link>
                    </div>
                </div>
            </header>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4 sm:gap-6">
                <StatCard title="Gross Scope" value={stats?.total || 0} icon={ClipboardList} color="bg-slate-400" />
                <StatCard title="Ready to Start" value={stats?.assigned || 0} icon={Clock} color="bg-sky-500" subText="Awaiting" />
                <StatCard title="Active Work" value={stats?.in_progress || 0} icon={PlayCircle} color="bg-indigo-500" subText="In-Progress" />
                <StatCard title="Review Queue" value={(stats?.pending || 0) + (stats?.submitted || 0)} icon={AlertCircle} color="bg-amber-500" subText="Attention" />
                <StatCard title="Completed" value={stats?.approved || 0} icon={CheckCircle} color="bg-emerald-500" subText="Approved" />
            </div>

            {filteredProjects.length > 0 && (
                <div className="space-y-6">
                    <div className="flex items-center gap-4 text-left">
                        <h2 className="text-2xl font-black tracking-tight text-foreground/80">
                            {selectedProjectId ? "Project Intelligence" : "Project Portfolio"}
                        </h2>
                        <div className="h-1 flex-1 bg-muted/20 rounded-full" />
                    </div>

                    <div className={cn(
                        "grid gap-8",
                        selectedProjectId ? "max-w-3xl mx-auto" : "grid-cols-1 md:grid-cols-2 xl:grid-cols-3"
                    )}>
                        {filteredProjects.map((p: any) => (
                            <div key={p.id} className={cn(
                                "transition-all duration-500 animate-in fade-in slide-in-from-bottom-4",
                                selectedProjectId && "scale-105"
                            )}>
                                <ProjectHealthWidget projectId={p.id} initialData={healthSummary[p.id]} />
                            </div>
                        ))}
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <Card className="lg:col-span-2 erp-card overflow-hidden bg-white">
                    <CardHeader className="flex flex-row items-center justify-between shrink-0 bg-slate-50/50 p-6 sm:p-8 border-b border-slate-100">
                        <div className="space-y-1 text-left">
                            <CardTitle className="text-2xl font-black tracking-tight text-foreground">Urgent Actions</CardTitle>
                            <CardDescription className="font-bold text-muted-foreground italic">Critical paths requiring your approval</CardDescription>
                        </div>
                        <div className="h-12 w-12 rounded-2xl bg-amber-100 flex items-center justify-center text-amber-600 shadow-inner">
                            <AlertCircle className="h-6 w-6" />
                        </div>
                    </CardHeader>
                    <CardContent className="p-0 overflow-y-auto no-scrollbar flex-1">
                        <div className="divide-y divide-slate-100">
                            {loading ? (
                                <div className="p-20"><Loading message="Synchronizing..." /></div>
                            ) : pendingTasks.length === 0 ? (
                                <div className="p-20 text-center flex flex-col items-center">
                                    <div className="h-24 w-24 bg-emerald-50 rounded-3xl flex items-center justify-center mb-6 shadow-inner text-emerald-500">
                                        <CheckCircle className="h-12 w-12" />
                                    </div>
                                    <h3 className="text-2xl font-black text-foreground">Clean Workspace</h3>
                                    <p className="text-muted-foreground font-bold mt-2 max-w-xs mx-auto italic">No high-priority blockers in your current context.</p>
                                </div>
                            ) : (
                                pendingTasks.map(task => (
                                    <div
                                        key={task.id}
                                        className="p-6 sm:p-8 hover:bg-slate-50 transition-all duration-300 flex flex-col sm:flex-row sm:items-center justify-between gap-6 group cursor-pointer relative"
                                        onClick={() => window.location.href = `/dms/tasks/${task.id}`}
                                    >
                                        <div className="flex gap-6 items-start overflow-hidden text-left">
                                            <div className={cn(
                                                "mt-2 h-4 w-4 rounded-full shrink-0 border-4 border-white shadow-xl transition-all group-hover:scale-125",
                                                task.status === 'PENDING' ? 'bg-amber-400' : 'bg-sky-400'
                                            )} />
                                            <div className="space-y-2 min-w-0 flex-1">
                                                <div className="flex items-center gap-3">
                                                    <span className="text-[10px] font-black uppercase tracking-widest px-3 py-1 rounded-lg bg-slate-100 text-slate-600">
                                                        {task.project_name}
                                                    </span>
                                                    <span className="text-[10px] font-black text-muted-foreground/40">
                                                        #{task.id}
                                                    </span>
                                                </div>
                                                <h4 className="font-black text-lg text-foreground/80 group-hover:text-primary transition-colors truncate">
                                                    {task.p6_activity_name || task.workflow_step_details?.action_description || 'Custom Assignment'}
                                                </h4>
                                                <p className="text-xs font-bold text-muted-foreground truncate italic">
                                                    {task.comments || "Instruction override active."}
                                                </p>
                                            </div>
                                        </div>
                                        <Button variant="ghost" size="sm" className="hidden sm:flex rounded-2xl font-black text-[10px] uppercase tracking-[0.2em] text-muted-foreground group-hover:text-primary group-hover:bg-primary/5 transition-all h-10 px-6 border-2 border-transparent group-hover:border-primary/10">
                                            Review Deck <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
                                        </Button>
                                    </div>
                                ))
                            )}
                        </div>
                    </CardContent>
                </Card>

                <div className="space-y-8">
                    <Card className="erp-card bg-slate-900 text-white overflow-hidden relative shadow-slate-900/20">
                        <div className="absolute top-0 right-0 w-32 h-32 bg-white/5 rounded-full -translate-y-1/2 translate-x-1/2" />
                        <CardHeader className="relative z-10 p-8 pb-4 text-left">
                            <CardTitle className="text-xl font-black uppercase tracking-[0.2em] opacity-80">Fast Connect</CardTitle>
                        </CardHeader>
                        <CardContent className="relative z-10 p-8 pt-0 grid gap-4">
                            {user.is_superuser && (
                                <Link to="/projects">
                                    <Button variant="secondary" className="w-full justify-start gap-4 h-14 font-black text-xs uppercase tracking-widest bg-white/10 hover:bg-white/20 text-white border-none rounded-2xl transition-all">
                                        <div className="p-2 rounded-xl bg-white/10"><ClipboardList className="h-5 w-5" /></div> Project Setup
                                    </Button>
                                </Link>
                            )}
                            {(user.is_owner || user.is_superuser) && (
                                <Link to="/team">
                                    <Button variant="secondary" className="w-full justify-start gap-4 h-14 font-black text-xs uppercase tracking-widest bg-white/10 hover:bg-white/20 text-white border-none rounded-2xl transition-all">
                                        <div className="p-2 rounded-xl bg-white/10"><Users className="h-5 w-5" /></div> Team Roster
                                    </Button>
                                </Link>
                            )}
                            <Link to="/planning/activities">
                                <Button variant="secondary" className="w-full justify-start gap-4 h-14 font-black text-xs uppercase tracking-widest bg-white/10 hover:bg-white/20 text-white border-none rounded-2xl transition-all">
                                    <div className="p-2 rounded-xl bg-white/10"><FileText className="h-5 w-5" /></div> P6 Registry
                                </Button>
                            </Link>
                        </CardContent>
                    </Card>

                    <Card className="erp-card border-2 border-dashed border-slate-200 bg-transparent shadow-none p-4">
                        <CardHeader className="p-4 pb-2 text-left">
                            <CardTitle className="text-[10px] font-black uppercase tracking-[0.3em] text-muted-foreground/50">Intelligence Stats</CardTitle>
                        </CardHeader>
                        <CardContent className="p-4 space-y-6 text-left">
                            <div className="flex gap-5 group/tip">
                                <div className="h-10 w-10 rounded-2xl bg-emerald-50 flex items-center justify-center shrink-0 shadow-inner group-hover/tip:bg-emerald-500 transition-all">
                                    <CheckCircle className="h-5 w-5 text-emerald-600 group-hover/tip:text-white" />
                                </div>
                                <div className="space-y-1">
                                    <p className="text-xs font-black text-foreground uppercase tracking-wider">Workflow Sync</p>
                                    <p className="text-[11px] font-bold text-muted-foreground leading-relaxed italic">Real-time status bridging active.</p>
                                </div>
                            </div>
                            <div className="flex gap-5 group/tip">
                                <div className="h-10 w-10 rounded-2xl bg-sky-50 flex items-center justify-center shrink-0 shadow-inner group-hover/tip:bg-sky-500 transition-all">
                                    <Clock className="h-5 w-5 text-sky-600 group-hover/tip:text-white" />
                                </div>
                                <div className="space-y-1">
                                    <p className="text-xs font-black text-foreground uppercase tracking-wider">SLA Guard</p>
                                    <p className="text-[11px] font-bold text-muted-foreground leading-relaxed italic">Priority flags active for idle tasks.</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
