import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
    Trophy,
    Zap,
    CheckCircle2,
    ArrowLeft,
    TrendingUp,
    Users,
    Star,
    Target
} from 'lucide-react';
import { Loading } from '@/components/Loading';
import { toast } from "sonner";
import { cn } from "@/lib/utils";

interface PerformanceMetric {
    user_id: number;
    username: string;
    full_name: string;
    tasks_completed: number;
    efficiency_days: number;
    tasks_with_p6: number;
    kpi_score: number;
}

interface Project {
    id: number;
    name: string;
    code: string;
}

export default function TeamPerformance() {
    const navigate = useNavigate();
    const [performance, setPerformance] = useState<PerformanceMetric[]>([]);
    const [projects, setProjects] = useState<Project[]>([]);
    const [selectedProject, setSelectedProject] = useState<string>('');
    const [selectedMonth, setSelectedMonth] = useState<string>(new Date().getMonth() + 1 + '');
    const [selectedYear, setSelectedYear] = useState<string>(new Date().getFullYear() + '');
    const [loading, setLoading] = useState(true);

    const fetchData = async () => {
        setLoading(true);
        try {
            let url = `/dms/team/performance/?month=${selectedMonth}&year=${selectedYear}`;
            if (selectedProject) url += `&project_id=${selectedProject}`;

            const [perfRes, projRes] = await Promise.all([
                api.get(url),
                api.get('/api/projects/?mode=my_projects')
            ]);
            setPerformance(perfRes.data.data);
            setProjects(projRes.data.data);
        } catch (e) {
            console.error(e);
            toast.error("Failed to load performance data");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, [selectedProject, selectedMonth, selectedYear]);

    if (loading && performance.length === 0) return <Loading fullPage message="Calculating Team KPIs..." />;

    const topPerformer = performance[0];

    return (
        <div className="max-w-7xl mx-auto space-y-8 pb-20 px-4 mt-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Header */}
            <div className="flex flex-col gap-4">
                <Button
                    variant="ghost"
                    size="sm"
                    className="w-fit gap-2 -ml-2 text-muted-foreground hover:text-foreground"
                    onClick={() => navigate('/owner/team')}
                >
                    <ArrowLeft className="h-4 w-4" /> Back to Team Management
                </Button>

                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 erp-header">
                    <div className="space-y-1">
                        <h1 className="text-2xl font-black tracking-tight text-foreground flex items-center gap-3">
                            <Trophy className="h-8 w-8 text-yellow-500" /> Team Performance
                        </h1>
                        <p className="text-sm font-bold text-muted-foreground italic pl-11">
                            Real-time efficiency tracking and KPI leaderboard based on P6 schedules.
                        </p>
                    </div>

                    <div className="flex flex-wrap items-center gap-3">
                        <div className="flex items-center gap-2 bg-muted/30 p-2 rounded-xl border border-primary/5">
                            <span className="text-[10px] uppercase font-black text-muted-foreground ml-2">Month</span>
                            <select
                                value={selectedMonth}
                                onChange={(e) => setSelectedMonth(e.target.value)}
                                className="bg-transparent border-none text-sm font-bold focus:ring-0 cursor-pointer"
                            >
                                {['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'].map((m, i) => (
                                    <option key={m} value={i + 1}>{m}</option>
                                ))}
                            </select>
                        </div>

                        <div className="flex items-center gap-2 bg-muted/30 p-2 rounded-xl border border-primary/5">
                            <span className="text-[10px] uppercase font-black text-muted-foreground ml-2">Year</span>
                            <select
                                value={selectedYear}
                                onChange={(e) => setSelectedYear(e.target.value)}
                                className="bg-transparent border-none text-sm font-bold focus:ring-0 cursor-pointer"
                            >
                                {[2024, 2025, 2026].map(y => (
                                    <option key={y} value={y}>{y}</option>
                                ))}
                            </select>
                        </div>

                        <div className="flex items-center gap-2 bg-muted/30 p-2 rounded-xl border border-primary/5">
                            <Target className="h-4 w-4 text-primary ml-2" />
                            <select
                                value={selectedProject}
                                onChange={(e) => setSelectedProject(e.target.value)}
                                className="bg-transparent border-none text-sm font-bold focus:ring-0 cursor-pointer min-w-[200px]"
                            >
                                <option value="">All Projects</option>
                                {projects.map(p => (
                                    <option key={p.id} value={p.id}>[{p.code}] {p.name}</option>
                                ))}
                            </select>
                        </div>
                    </div>
                </div>
            </div>

            {/* Top Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card className="erp-card bg-gradient-to-br from-yellow-50 to-orange-50 dark:from-yellow-950/20 dark:to-orange-950/20 border-yellow-200/50 shadow-sm relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-4 opacity-10 scale-150 rotate-12 transition-transform group-hover:scale-[2] duration-700">
                        <Star className="h-20 w-20 text-yellow-500" />
                    </div>
                    <CardHeader className="pb-2 relative">
                        <CardTitle className="text-[10px] font-black uppercase tracking-widest text-yellow-700 dark:text-yellow-500">Current MVP</CardTitle>
                    </CardHeader>
                    <CardContent className="relative">
                        <p className="text-2xl font-black text-yellow-900 dark:text-yellow-100">{topPerformer?.full_name || "N/A"}</p>
                        <div className="flex items-center gap-2 mt-2">
                            <div className="bg-yellow-500 text-white text-[10px] font-black px-2 py-0.5 rounded-full shadow-lg shadow-yellow-500/20 uppercase tracking-widest">
                                {topPerformer?.kpi_score || 0} KPI Points
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card className="erp-card border-primary/5 shadow-sm bg-card ring-1 ring-primary/5">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-[10px] font-black uppercase tracking-widest text-primary/60">Department Velocity</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="flex items-baseline gap-2">
                            <p className="text-3xl font-black text-foreground">
                                {performance.reduce((acc, curr) => acc + curr.tasks_completed, 0)}
                            </p>
                            <span className="text-[10px] font-black text-muted-foreground uppercase tracking-widest opacity-60">Tasks Closed</span>
                        </div>
                        <p className="text-[10px] font-bold text-muted-foreground mt-2 flex items-center gap-1 italic opacity-70">
                            <Zap className="h-3 w-3 text-yellow-500" /> Combined Efficiency
                        </p>
                    </CardContent>
                </Card>

                <Card className="erp-card border-primary/5 shadow-sm bg-card ring-1 ring-primary/5">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-[10px] font-black uppercase tracking-widest text-muted-foreground/60">Team Size</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="flex items-baseline gap-2">
                            <p className="text-3xl font-black text-foreground">{performance.length}</p>
                            <span className="text-[10px] font-black text-muted-foreground uppercase tracking-widest opacity-60">Active Members</span>
                        </div>
                        <p className="text-[10px] font-bold text-muted-foreground mt-2 flex items-center gap-1 italic opacity-70">
                            <Users className="h-3 w-3 text-primary" /> Tracked Specialists
                        </p>
                    </CardContent>
                </Card>
            </div>

            {/* Leaderboard Table */}
            <Card className="border-primary/10 shadow-xl">
                <CardHeader className="border-b bg-muted/30">
                    <CardTitle className="text-xl font-black flex items-center gap-2">
                        <TrendingUp className="h-5 w-5 text-green-600" /> Efficiency Leaderboard
                    </CardTitle>
                    <CardDescription>Monthly performance metrics based on actual vs estimated completion dates.</CardDescription>
                </CardHeader>
                <CardContent className="p-0">
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="bg-muted/50 text-left">
                                    <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-muted-foreground">Rank</th>
                                    <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-muted-foreground">Teammate</th>
                                    <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-muted-foreground text-center">Tasks</th>
                                    <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-muted-foreground text-center">Efficiency (Days)</th>
                                    <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-muted-foreground text-right font-black text-primary">KPI SCORE</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y">
                                {performance.map((p, index) => (
                                    <tr key={p.user_id} className={cn(
                                        "hover:bg-muted/30 transition-colors group",
                                        index === 0 ? "bg-yellow-50/30" : ""
                                    )}>
                                        <td className="px-6 py-4">
                                            <div className={cn(
                                                "h-8 w-8 rounded-lg flex items-center justify-center font-black text-sm border-2",
                                                index === 0 ? "bg-yellow-500 text-white border-yellow-400 rotate-3 shadow-md" :
                                                    index === 1 ? "bg-slate-300 text-slate-800 border-slate-200" :
                                                        index === 2 ? "bg-amber-600 text-white border-amber-500" :
                                                            "bg-muted text-muted-foreground border-transparent"
                                            )}>
                                                {index + 1}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-3">
                                                <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center font-black text-primary group-hover:scale-110 transition-transform">
                                                    {p.full_name[0]}
                                                </div>
                                                <div>
                                                    <p className="font-black text-foreground">{p.full_name}</p>
                                                    <p className="text-xs font-medium text-muted-foreground">@{p.username}</p>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            <div className="flex flex-col items-center">
                                                <span className="font-black text-foreground">{p.tasks_completed}</span>
                                                <span className="text-[9px] font-bold text-muted-foreground uppercase">Verified</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            <div className={cn(
                                                "inline-flex flex-col items-center px-3 py-1 rounded-lg border",
                                                p.efficiency_days > 0 ? "bg-green-50 border-green-100 text-green-700" :
                                                    p.efficiency_days < 0 ? "bg-red-50 border-red-100 text-red-700" :
                                                        "bg-muted/50 border-transparent text-muted-foreground"
                                            )}>
                                                <span className="font-black flex items-center gap-1">
                                                    {p.efficiency_days > 0 ? `+${p.efficiency_days}` : p.efficiency_days}
                                                    {p.efficiency_days > 5 && <Zap className="h-3 w-3 fill-current" />}
                                                </span>
                                                <span className="text-[9px] font-bold uppercase tracking-tighter">
                                                    {p.efficiency_days > 0 ? "Ahead of P6" : p.efficiency_days < 0 ? "Total Delay" : "On Schedule"}
                                                </span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <span className="text-lg font-black text-primary font-mono tracking-tighter">
                                                {p.kpi_score.toLocaleString()}
                                            </span>
                                        </td>
                                    </tr>
                                ))}

                                {performance.length === 0 && !loading && (
                                    <tr>
                                        <td colSpan={5} className="px-6 py-20 text-center">
                                            <div className="max-w-xs mx-auto space-y-3">
                                                <Zap className="h-12 w-12 text-muted-foreground/20 mx-auto" />
                                                <p className="font-bold text-muted-foreground text-lg">No performance data yet.</p>
                                                <p className="text-xs text-muted-foreground/60">KPIs are generated when tasks linked to P6 activities are APPROVED by the HOD.</p>
                                            </div>
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </CardContent>
            </Card>

            {/* Scoring Legend */}
            <div className="bg-muted/20 rounded-2xl p-6 border border-primary/5 flex flex-col md:flex-row gap-8 items-center justify-between">
                <div className="space-y-1">
                    <h4 className="text-sm font-black uppercase tracking-widest flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4 text-primary" /> KPI Reward Formula
                    </h4>
                    <p className="text-xs text-muted-foreground font-medium">Standardized across all PIC ERP departments.</p>
                </div>
                <div className="flex gap-4 md:gap-12">
                    <div className="text-center">
                        <p className="text-lg font-black text-primary">+10</p>
                        <p className="text-[10px] font-bold text-muted-foreground uppercase">Per Task</p>
                    </div>
                    <div className="text-center">
                        <p className="text-lg font-black text-green-600">+5</p>
                        <p className="text-[10px] font-bold text-muted-foreground uppercase">Per Early Day</p>
                    </div>
                    <div className="text-center">
                        <p className="text-lg font-black text-foreground">1.0x</p>
                        <p className="text-[10px] font-bold text-muted-foreground uppercase">HOD Multiplier</p>
                    </div>
                </div>
            </div>
        </div>
    );
}

