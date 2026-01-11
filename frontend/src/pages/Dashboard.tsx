import { useState, useEffect } from 'react';
import api from '@/services/api';
import { useAuthStore } from '@/hooks/useAuthStore';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { AlertCircle, ArrowRight, CheckCircle, ClipboardList, Clock, Users, FileText } from 'lucide-react';
import { Loading } from '@/components/Loading';
import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';

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
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [pendingTasks, setPendingTasks] = useState<Task[]>([]);
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
        try {
            const [statsRes, tasksRes] = await Promise.all([
                api.get(`/dms/tasks/dashboard_stats/?mode=${mode}`),
                // For pending action, we fetch tasks that need attention based on role
                api.get(`/dms/tasks/?mode=${mode}&status=${mode === 'department' ? 'PENDING' : 'SUBMITTED'}`)
            ]);
            setStats(statsRes.data);
            setPendingTasks(tasksRes.data.results || tasksRes.data); // Handle paginated or non-paginated
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (user) fetchDashboardData();
    }, [user]);

    if (!user) return null;

    const StatCard = ({ title, value, icon: Icon, color }: any) => (
        <Card className="border-none shadow-sm bg-white overflow-hidden">
            <div className={`h-1 w-full ${color}`} />
            <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                    <div>
                        <p className="text-sm font-medium text-muted-foreground">{title}</p>
                        <p className="text-2xl font-bold mt-1">{value}</p>
                    </div>
                    <div className={`p-2 rounded-lg bg-opacity-10 ${color.replace('bg-', 'text-')} bg-current`}>
                        <Icon className="h-5 w-5" />
                    </div>
                </div>
            </CardContent>
        </Card>
    );

    return (
        <div className="space-y-8 max-w-[1600px] mx-auto">
            <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-3xl font-extrabold tracking-tight text-foreground">
                        Welcome back, {user.first_name}!
                    </h1>
                    <p className="text-muted-foreground mt-1">
                        {user.is_superuser ? 'System Administrator Overview' :
                            user.is_owner ? 'Project Management Dashboard' :
                                user.is_hod ? 'Departmental Control Panel' : 'Team Member Dashboard'}
                    </p>
                </div>
                <div className="flex gap-3">
                    <Button variant="outline" onClick={fetchDashboardData}>Refresh Data</Button>
                    <Link to="/dms">
                        <Button>View All Tasks</Button>
                    </Link>
                </div>
            </header>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard
                    title="Total Tasks"
                    value={stats?.total || 0}
                    icon={ClipboardList}
                    color="bg-blue-500"
                />
                <StatCard
                    title="Action Required"
                    value={(stats?.pending || 0) + (stats?.submitted || 0)}
                    icon={AlertCircle}
                    color="bg-orange-500"
                />
                <StatCard
                    title="In Progress"
                    value={(stats?.assigned || 0) + (stats?.in_progress || 0)}
                    icon={Clock}
                    color="bg-indigo-500"
                />
                <StatCard
                    title="Completed"
                    value={stats?.approved || 0}
                    icon={CheckCircle}
                    color="bg-green-500"
                />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Pending Actions List */}
                <Card className="lg:col-span-2 border-primary/5 shadow-md flex flex-col max-h-[600px]">
                    <CardHeader className="flex flex-row items-center justify-between shrink-0">
                        <div>
                            <CardTitle>Pending Approvals & Assignments</CardTitle>
                            <CardDescription>Items that require your immediate attention</CardDescription>
                        </div>
                        <AlertCircle className="h-5 w-5 text-orange-500" />
                    </CardHeader>
                    <CardContent className="p-0 overflow-y-auto no-scrollbar flex-1">
                        <div className="divide-y divide-muted/50">
                            {loading ? (
                                <Loading message="Updating metrics..." />
                            ) : pendingTasks.length === 0 ? (
                                <div className="p-12 text-center">
                                    <div className="inline-flex p-3 rounded-full bg-green-50 text-green-600 mb-3">
                                        <CheckCircle className="h-6 w-6" />
                                    </div>
                                    <p className="font-medium text-foreground">You're all caught up!</p>
                                    <p className="text-sm text-muted-foreground mt-1">No pending tasks found for your current role.</p>
                                </div>
                            ) : (
                                pendingTasks.map(task => (
                                    <div key={task.id} className="p-4 hover:bg-muted/30 transition-colors flex items-center justify-between group">
                                        <div className="flex gap-4 items-start overflow-hidden">
                                            <div className={`mt-1.5 h-2 w-2 rounded-full shrink-0 ${task.status === 'PENDING' ? 'bg-orange-400' : 'bg-blue-400'}`} />
                                            <div className="overflow-hidden">
                                                <div className="flex items-center gap-2 flex-wrap">
                                                    <span className="text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-muted shrink-0">
                                                        {task.project_name}
                                                    </span>
                                                    <span className="text-xs font-mono font-semibold text-muted-foreground shrink-0">
                                                        {task.workflow_step_details?.sequence_id || 'AD-HOC'}
                                                    </span>
                                                </div>
                                                <h4 className="font-bold text-sm mt-1 text-foreground truncate max-w-full">
                                                    {task.p6_activity_name || task.workflow_step_details?.action_description || 'Custom Assignment'}
                                                </h4>
                                                <p className="text-xs text-muted-foreground mt-1 truncate max-w-full italic">
                                                    {task.workflow_step_details?.action_description ? `Step: ${task.workflow_step_details.action_description}` : task.comments || 'No details provided.'}
                                                </p>
                                            </div>
                                        </div>
                                        <Link to="/dms" className="shrink-0 ml-4">
                                            <Button variant="ghost" size="sm" className="opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                                                Review <ArrowRight className="ml-2 h-3 w-3" />
                                            </Button>
                                        </Link>
                                    </div>
                                ))
                            )}
                        </div>
                    </CardContent>
                </Card>

                {/* Quick Actions & Tips */}
                <div className="space-y-6">
                    <Card className="bg-primary/5 border-none">
                        <CardHeader>
                            <CardTitle className="text-lg">Quick Access</CardTitle>
                        </CardHeader>
                        <CardContent className="grid gap-2">
                            {user.is_superuser && (
                                <Link to="/projects">
                                    <Button variant="outline" className="w-full justify-start gap-2 bg-white">
                                        <ClipboardList className="h-4 w-4" /> Go to Project Setup
                                    </Button>
                                </Link>
                            )}
                            {(user.is_owner || user.is_superuser) && (
                                <Link to="/team">
                                    <Button variant="outline" className="w-full justify-start gap-2 bg-white">
                                        <Users className="h-4 w-4" /> Manage Team
                                    </Button>
                                </Link>
                            )}
                            <Link to="/planning/activities">
                                <Button variant="outline" className="w-full justify-start gap-2 bg-white">
                                    <FileText className="h-4 w-4" /> P6 Activity Registry
                                </Button>
                            </Link>
                        </CardContent>
                    </Card>

                    <Card className="border-dashed">
                        <CardHeader>
                            <CardTitle className="text-sm font-semibold">Dashboard Insights</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4 text-xs text-muted-foreground">
                            <div className="flex gap-3">
                                <div className="h-2 w-2 rounded-full bg-green-500 mt-1 shrink-0" />
                                <p><strong>Tip:</strong> Approved tasks automatically trigger the next step in the workflow for the relevant department.</p>
                            </div>
                            <div className="flex gap-3">
                                <div className="h-2 w-2 rounded-full bg-blue-500 mt-1 shrink-0" />
                                <p><strong>Flow:</strong> When a Team Member submits a document, it appears here for HOD/Owner approval.</p>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
