import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import api from '@/services/api';
import { CheckCircle, Clock, PlayCircle, ArrowRight, TrendingUp, TrendingDown, Zap, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';
import { cn } from '@/lib/utils';

export interface HealthData {
    schedule_status: string;
    tasks_total: number;
    tasks_completed: number;
    tasks_waiting?: number;
    tasks_in_progress?: number;
    tasks_overdue: number;
    activities_total: number;
    activities_delayed: number;
    my_tasks_total: number;
    my_tasks_completed: number;
    my_tasks_waiting?: number;
    my_tasks_in_progress?: number;
    my_tasks_active: number;
    my_tasks_overdue: number;
    project_id?: number;
    project_name?: string;
}

export function ProjectHealthWidget({ projectId, initialData }: { projectId: number, initialData?: HealthData }) {
    const [data, setData] = useState<HealthData | null>(initialData || null);
    const [loading, setLoading] = useState(!initialData);
    const [tab, setTab] = useState<'personal' | 'global'>('personal');

    useEffect(() => {
        if (initialData) {
            setData(initialData);
            setLoading(false);
            return;
        }

        const fetchData = async () => {
            try {
                const response = await api.get(`/api/projects/${projectId}/health/`);
                setData(response.data.data);
            } catch (error) {
                console.error("Failed to fetch project health", error);
            } finally {
                setLoading(false);
            }
        };

        if (projectId) {
            fetchData();
        }
    }, [projectId, initialData]);

    if (!projectId) return null;
    if (loading) return (
        <Card className="h-full flex items-center justify-center p-6 border-dashed animate-pulse bg-muted/5">
            <div className="flex flex-col items-center gap-2">
                <Zap className="h-5 w-5 text-primary/20" />
                <span className="text-muted-foreground font-black text-[10px] uppercase tracking-widest">Gathering Intelligence...</span>
            </div>
        </Card>
    );
    if (!data) return <div className="p-4 text-xs font-bold text-muted-foreground uppercase italic text-center">Data Link Offline</div>;

    const isPersonal = tab === 'personal';
    const total = isPersonal ? data.my_tasks_total : data.tasks_total;
    const completed = isPersonal ? data.my_tasks_completed : data.tasks_completed;
    const waiting = isPersonal ? (data.my_tasks_waiting ?? 0) : (data.tasks_waiting ?? 0);
    const active = isPersonal ? (data.my_tasks_in_progress ?? data.my_tasks_active) : (data.tasks_in_progress ?? 0);
    const overdue = isPersonal ? data.my_tasks_overdue : data.tasks_overdue;

    // Health Heuristic Calculation
    const overdueRatio = total > 0 ? (overdue / total) : 0;
    const isCritical = overdueRatio > 0.15 || data.schedule_status === 'Behind Schedule';
    const isWarning = overdueRatio > 0 && overdueRatio <= 0.15;
    const isHealthy = !isCritical && !isWarning;

    const progressPercent = total > 0 ? Math.round((completed / total) * 100) : 0;

    // Radial Progress Calculation
    const radius = 38;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (progressPercent / 100) * circumference;

    return (
        <Card className="erp-card bg-card group hover:shadow-2xl hover:shadow-primary/5 transition-all duration-500 overflow-hidden ring-1 ring-primary/5 relative">
            {/* Actionable Health Bar */}
            <div className={cn(
                "absolute top-0 left-0 w-full h-1.5 transition-colors duration-500",
                isCritical ? "bg-red-500" : isWarning ? "bg-amber-500" : "bg-emerald-500"
            )} />

            <CardHeader className="pb-4 pt-8 px-8">
                <div className="flex items-center justify-between gap-6">
                    <div className="space-y-1.5 min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                            <h3 className="text-xs font-black tracking-[0.2em] text-muted-foreground/40 uppercase truncate">{data.project_name || "Enterprise Segment"}</h3>
                            {isCritical && <AlertTriangle className="h-3 w-3 text-red-500 animate-bounce" />}
                        </div>
                        <div className="flex items-center gap-3">
                            <div className={cn(
                                "h-2.5 w-2.5 rounded-full shadow-lg transition-all duration-500",
                                isCritical ? "bg-red-500 shadow-red-500/50" : isWarning ? "bg-amber-500 shadow-amber-500/50" : "bg-emerald-500 shadow-emerald-500/50"
                            )} />
                            <span className={cn(
                                "text-[11px] font-black uppercase tracking-widest",
                                isCritical ? "text-red-600" : isWarning ? "text-amber-600" : "text-emerald-600"
                            )}>
                                {isCritical ? "Critical Performance" : isWarning ? "Attention Required" : "Delivery Optimal"}
                            </span>
                        </div>
                    </div>

                    <div className="flex bg-muted/30 p-1 rounded-2xl erp-glass backdrop-blur-md self-start border border-primary/5">
                        {(['personal', 'global'] as const).map((t) => (
                            <button
                                key={t}
                                onClick={() => setTab(t)}
                                className={cn(
                                    "px-4 py-2 text-[9px] font-black uppercase tracking-widest rounded-xl transition-all",
                                    tab === t ? "bg-card shadow-xl text-primary scale-100" : "text-muted-foreground/30 hover:text-muted-foreground/60"
                                )}
                            >
                                {t === 'personal' ? 'My Scope' : 'Total Scope'}
                            </button>
                        ))}
                    </div>
                </div>
            </CardHeader>

            <CardContent className="px-8 pb-8 pt-2 space-y-8">
                <div className="flex items-center gap-10">
                    {/* Radial Guage - Primary Information */}
                    <div className="relative flex items-center justify-center shrink-0 w-28 h-28">
                        <svg className="w-28 h-28 transform -rotate-90 filter drop-shadow-sm">
                            <circle
                                cx="56"
                                cy="56"
                                r={radius}
                                stroke="currentColor"
                                strokeWidth="10"
                                fill="transparent"
                                className="text-muted/10 dark:text-muted/5"
                            />
                            <circle
                                cx="56"
                                cy="56"
                                r={radius}
                                stroke="currentColor"
                                strokeWidth="10"
                                strokeDasharray={circumference}
                                strokeDashoffset={offset}
                                strokeLinecap="round"
                                fill="transparent"
                                className={cn(
                                    "transition-all duration-1000 ease-out",
                                    isCritical ? "text-red-500" : isWarning ? "text-amber-500" : "text-emerald-500"
                                )}
                            />
                        </svg>
                        <div className="absolute flex flex-col items-center">
                            <span className="text-2xl font-black tracking-tighter text-foreground">{progressPercent}%</span>
                            <span className="text-[8px] font-black uppercase tracking-widest text-muted-foreground opacity-60">Ready</span>
                        </div>
                    </div>

                    {/* Metadata 2x2 Grid - Contextual Information */}
                    <div className="grid grid-cols-2 gap-x-8 gap-y-6 flex-1">
                        <div className="space-y-1">
                            <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground/40">Total Scope</p>
                            <p className="text-xl font-black tracking-tighter text-foreground/80">{total}</p>
                        </div>
                        <div className="space-y-1 text-right">
                            <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground/40 text-right">Delivery Pace</p>
                            <div className="flex items-center justify-end gap-1.5 font-black text-xs">
                                {isHealthy ? <TrendingUp className="h-4 w-4 text-emerald-500" /> : <TrendingDown className="h-4 w-4 text-red-500" />}
                                <span className={cn(isHealthy ? "text-emerald-600" : "text-red-600")}>
                                    {isHealthy ? "Steady" : "Delayed"}
                                </span>
                            </div>
                        </div>
                        <div className="space-y-1">
                            <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground/40">Finalized</p>
                            <p className="text-xl font-black tracking-tighter text-emerald-600/80">{completed}</p>
                        </div>
                        <div className="space-y-1 text-right">
                            <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground/40">Actionable Risk</p>
                            <p className={cn(
                                "text-xl font-black tracking-tighter",
                                overdue > 0 ? "text-red-600 shadow-sm" : "text-foreground/40"
                            )}>
                                {overdue}
                            </p>
                        </div>
                    </div>
                </div>

                {/* Tactical Metrics - Live State */}
                <div className="grid grid-cols-3 gap-4">
                    <div className="p-4 rounded-[1.5rem] bg-slate-50 border border-slate-100 dark:bg-slate-900/40 dark:border-slate-800 flex flex-col items-center justify-center gap-2 transition-all hover:bg-slate-100 dark:hover:bg-slate-800/60 shadow-inner group/item">
                        <div className="h-8 w-8 rounded-xl bg-white dark:bg-slate-800 flex items-center justify-center shadow-sm group-hover/item:scale-110 transition-transform">
                            <Clock className="h-4 w-4 text-slate-400 group-hover/item:text-primary transition-colors" />
                        </div>
                        <div className="text-center">
                            <p className="text-base font-black text-slate-700 dark:text-slate-300 leading-none">{waiting}</p>
                            <p className="text-[9px] uppercase font-black text-slate-400 tracking-tighter mt-1">Staged</p>
                        </div>
                    </div>
                    <div className="p-4 rounded-[1.5rem] bg-indigo-50 border border-indigo-100 dark:bg-indigo-900/20 dark:border-indigo-800 flex flex-col items-center justify-center gap-2 transition-all hover:bg-indigo-100 dark:hover:bg-indigo-800/40 shadow-inner group/item">
                        <div className="h-8 w-8 rounded-xl bg-white dark:bg-slate-800 flex items-center justify-center shadow-sm group-hover/item:scale-110 transition-transform">
                            <PlayCircle className="h-4 w-4 text-primary group-hover/item:animate-pulse" />
                        </div>
                        <div className="text-center">
                            <p className="text-base font-black text-primary leading-none">{active}</p>
                            <p className="text-[9px] uppercase font-black text-primary/40 tracking-tighter mt-1">Live Ops</p>
                        </div>
                    </div>
                    <div className="p-4 rounded-[1.5rem] bg-emerald-50 border border-emerald-100 dark:bg-emerald-900/20 dark:border-emerald-800 flex flex-col items-center justify-center gap-2 transition-all hover:bg-emerald-100 dark:hover:bg-emerald-800/40 shadow-inner group/item">
                        <div className="h-8 w-8 rounded-xl bg-white dark:bg-slate-800 flex items-center justify-center shadow-sm group-hover/item:scale-110 transition-transform">
                            <CheckCircle className="h-4 w-4 text-emerald-500 transition-colors" />
                        </div>
                        <div className="text-center">
                            <p className="text-base font-black text-emerald-700 dark:text-emerald-300 leading-none">{completed}</p>
                            <p className="text-[9px] uppercase font-black text-emerald-400 tracking-tighter mt-1">Synced</p>
                        </div>
                    </div>
                </div>

                <div className="pt-4 border-t border-primary/5">
                    <Link to={`/dms?project=${projectId}`}>
                        <Button className="w-full h-14 rounded-2xl text-[11px] font-black uppercase tracking-[0.25em] shadow-xl shadow-primary/20 hover:scale-[1.02] transition-all duration-300 gap-3 group/btn">
                            Enter Tactical Workspace <ArrowRight className="h-4 w-4 group-hover/btn:translate-x-1.5 transition-transform" />
                        </Button>
                    </Link>
                </div>
            </CardContent>
        </Card>
    );
}
