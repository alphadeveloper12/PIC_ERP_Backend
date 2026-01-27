import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '@/services/api';
import { useAuthStore } from '@/hooks/useAuthStore';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import {
    Check,
    UserPlus,
    Clock,
    FileText,
    Plus,
    MoreHorizontal,
    Upload,
    ChevronDown,
    Play,
    Download
} from 'lucide-react';
import { Loading } from '@/components/Loading';
import { TaskCardSkeleton } from '@/components/dms/TaskCardSkeleton';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import { toast } from "sonner";
import { usePermissions } from "@/lib/permissions";

interface Document {
    id: number;
    file: string;
    document_type: string;
    uploaded_by: {
        first_name: string;
        last_name: string;
    };
    created_at: string;
}

interface Task {
    id: number;
    workflow_step_details?: {
        sequence_id: string;
        action_description: string;
    };
    project_name: string;
    p6_activity_name?: string;
    project: number;
    status: string;
    comments: string;
    assigned_to_details?: {
        username: string;
        first_name: string;
        last_name: string;
    };
    created_at: string;
    documents: Document[];
    related_documents?: Document[];
    due_date?: string;
    early_start?: string;
    early_finish?: string;
    late_start?: string;
    late_finish?: string;
    actual_start?: string;
    actual_finish?: string;
}

interface User {
    id: number;
    username: string;
    first_name: string;
    last_name: string;
}

interface Project {
    id: number;
    name: string;
}

export default function TaskDashboard() {
    const { user } = useAuthStore();
    const { hasPermission } = usePermissions();
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState(false);
    const [tasks, setTasks] = useState<Task[]>([]);
    const [expandedTask, setExpandedTask] = useState<number | null>(null);
    const [activeTab, setActiveTab] = useState<'my_tasks' | 'department' | 'all_tasks' | 'project_owner'>('my_tasks');

    // New Custom Task State
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [projects, setProjects] = useState<Project[]>([]);
    const [teamMembers, setTeamMembers] = useState<User[]>([]);
    const [newTask, setNewTask] = useState({
        project: '',
        action_description: '',
        comments: '',
        assigned_to: ''
    });

    // Expansion & Action State
    const [actionComment, setActionComment] = useState('');
    const [assigneeId, setAssigneeId] = useState('');
    const [selectedFile, setSelectedFile] = useState<File | null>(null);

    // Bulk State
    const [selectedTasks, setSelectedTasks] = useState<number[]>([]);
    const [departments, setDepartments] = useState<{ id: number; name: string }[]>([]);
    const [bulkAssignee, setBulkAssignee] = useState('');
    const [bulkDepartment, setBulkDepartment] = useState('');

    const fetchTasks = async () => {
        setLoading(true);
        try {
            const res = await api.get(`/dms/tasks/?mode=${activeTab}`);
            setTasks(res.data.results || res.data);
        } catch (e) {
            console.error(e);
            toast.error("Failed to fetch tasks");
        } finally {
            setLoading(false);
        }
    };

    const fetchMeta = async () => {
        try {
            const projRes = await api.get('/api/projects/?mode=my_projects');
            setProjects(projRes.data.data);

            const teamRes = await api.get('/dms/team/?page_size=100');
            const data = teamRes.data.results || teamRes.data;
            setTeamMembers(data.map((r: any) => ({
                id: r.user,
                ...r.user_details
            })));

            // Departments for Owner
            const deptRes = await api.get('/dms/departments/');
            setDepartments(deptRes.data.results || deptRes.data);

        } catch (e) {
            console.error(e);
        }
    };

    const fetchTeamForProject = async (projectId: number) => {
        try {
            const teamRes = await api.get(`/dms/team/?project_id=${projectId}&page_size=100`);
            const data = teamRes.data.results || teamRes.data;
            setTeamMembers(data.map((r: any) => ({
                id: r.user,
                ...r.user_details
            })));
        } catch (e) {
            console.error("Failed to fetch project team", e);
        }
    };

    useEffect(() => {
        fetchTasks();
    }, [activeTab]);

    useEffect(() => {
        if (user) fetchMeta();

        // Default tab based on role
        if (user?.is_owner) setActiveTab('project_owner');
        else if (user?.is_hod) setActiveTab('department');
        else setActiveTab('my_tasks');
    }, [user]);

    const handleExpand = (task: Task) => {
        if (expandedTask === task.id) {
            setExpandedTask(null);
        } else {
            setExpandedTask(task.id);
            // Fetch team specifically for this project so assignee list isn't empty
            fetchTeamForProject(task.project);
        }
    };

    const handleCreateCustomTask = async () => {
        setActionLoading(true);
        try {
            await api.post('/dms/tasks/', {
                project: newTask.project,
                status: newTask.assigned_to ? 'ASSIGNED' : 'PENDING',
                assigned_to: newTask.assigned_to || null,
                comments: newTask.comments
                // workflow_step is null for custom tasks
            });
            toast.success("Custom task created and assigned");
            setIsCreateModalOpen(false);
            fetchTasks();
        } catch (e) {
            console.error(e);
            toast.error("Failed to create task");
        } finally {
            setActionLoading(false);
        }
    };

    const handleAction = async (taskId: number, action: string) => {
        setActionLoading(true);
        try {
            const payload: any = {
                action,
                comments: actionComment
            };
            if (action === 'ASSIGN') {
                payload.assigned_to = parseInt(assigneeId);
            }

            await api.post(`/dms/tasks/${taskId}/perform_action/`, payload);
            toast.success(`Task status updated: ${action}`);
            setExpandedTask(null);
            setActionComment('');
            fetchTasks();
        } catch (e: any) {
            console.error(e);
            const errorData = e.response?.data;
            const msg = errorData?.error || (typeof errorData === 'object' ? JSON.stringify(errorData) : errorData) || e.message || "Action failed";
            toast.error(msg);
        } finally {
            setActionLoading(false);
        }
    };

    const toggleSelectAll = () => {
        if (selectedTasks.length === tasks.length) setSelectedTasks([]);
        else setSelectedTasks(tasks.map(t => t.id));
    };

    const toggleSelect = (id: number) => {
        if (selectedTasks.includes(id)) setSelectedTasks(selectedTasks.filter(tid => tid !== id));
        else setSelectedTasks([...selectedTasks, id]);
    };

    const handleBulkAssignMember = async () => {
        if (!bulkAssignee || selectedTasks.length === 0) return;
        setActionLoading(true);
        try {
            await api.post('/dms/tasks/bulk_assign_member/', {
                task_ids: selectedTasks,
                assigned_to: parseInt(bulkAssignee)
            });
            toast.success(`Assigned ${selectedTasks.length} tasks successfully`);
            setSelectedTasks([]);
            setBulkAssignee('');
            fetchTasks();
        } catch (e) {
            console.error(e);
            toast.error("Bulk assignment failed");
        } finally {
            setActionLoading(false);
        }
    };

    const handleBulkAssignDept = async () => {
        if (!bulkDepartment || selectedTasks.length === 0) return;
        setActionLoading(true);
        try {
            await api.post('/dms/tasks/bulk_assign_department/', {
                task_ids: selectedTasks,
                department_id: parseInt(bulkDepartment)
            });
            toast.success(`Re-assigned ${selectedTasks.length} tasks to department`);
            setSelectedTasks([]);
            setBulkDepartment('');
            fetchTasks();
        } catch (e: any) {
            console.error(e);
            toast.error(e.response?.data?.error || "Bulk re-assignment failed");
        } finally {
            setActionLoading(false);
        }
    };

    const handleUpload = async (taskId: number) => {
        if (!selectedFile) return;
        setActionLoading(true);
        const formData = new FormData();
        formData.append('task', taskId.toString());
        formData.append('file', selectedFile);
        formData.append('document_type', 'Work Submission');

        try {
            await api.post('/dms/documents/', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            toast.success("Document uploaded successfully");
            setSelectedFile(null);
        } catch (e) {
            console.error(e);
            toast.error("Upload failed");
        } finally {
            setActionLoading(false);
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'PENDING': return 'bg-orange-100 text-orange-700 border-orange-200';
            case 'ASSIGNED': return 'bg-blue-100 text-blue-700 border-blue-200';
            case 'IN_PROGRESS': return 'bg-indigo-100 text-indigo-700 border-indigo-200';
            case 'SUBMITTED': return 'bg-purple-100 text-purple-700 border-purple-200';
            case 'APPROVED': return 'bg-green-100 text-green-700 border-green-200';
            case 'REJECTED': return 'bg-red-100 text-red-700 border-red-200';
            case 'RETURNED': return 'bg-orange-100 text-orange-700 border-orange-200 animate-pulse';
            default: return 'bg-gray-100 text-gray-700 border-gray-200';
        }
    };

    return (
        <div className="space-y-8 max-w-[1600px] mx-auto pb-32">
            {actionLoading && <Loading fullPage message="Processing..." />}
            <header className="erp-header flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                <div className="space-y-1">
                    <h1 className="text-2xl font-black tracking-tight text-foreground">Task Registry</h1>
                    <p className="text-sm font-bold text-muted-foreground italic">Manage workflow progression and task assignments across projects.</p>
                </div>

                <div className="flex items-center gap-3">
                    {/* ... (Create Modal kept same) ... */}
                    {(user?.is_owner || user?.is_hod || user?.is_superuser) && (
                        <Dialog open={isCreateModalOpen} onOpenChange={setIsCreateModalOpen}>
                            <DialogTrigger asChild>
                                <Button className="h-11 px-6 shadow-lg gap-2">
                                    <Plus className="h-5 w-5" /> Create Custom Task
                                </Button>
                            </DialogTrigger>
                            <DialogContent className="sm:max-w-[500px]">
                                <DialogHeader>
                                    <DialogTitle>New Custom Assignment</DialogTitle>
                                    <DialogDescription>Create a task outside the standard P6 workflow.</DialogDescription>
                                </DialogHeader>
                                <div className="grid gap-6 py-4">
                                    <div className="grid gap-2">
                                        <Label>Target Project</Label>
                                        <select
                                            className="h-10 w-full rounded-md border border-input px-3 bg-background text-sm"
                                            value={newTask.project}
                                            onChange={e => {
                                                setNewTask({ ...newTask, project: e.target.value });
                                                if (e.target.value) fetchTeamForProject(parseInt(e.target.value));
                                            }}
                                        >
                                            <option value="">Select Project</option>
                                            {projects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                                        </select>
                                    </div>
                                    <div className="grid gap-2">
                                        <Label>Quick Description / Instruction</Label>
                                        <Input
                                            placeholder="What needs to be done?"
                                            value={newTask.comments}
                                            onChange={e => setNewTask({ ...newTask, comments: e.target.value })}
                                        />
                                    </div>
                                    <div className="grid gap-2">
                                        <Label>Assign To (Optional)</Label>
                                        <select
                                            className="h-10 w-full rounded-md border border-input px-3 bg-background text-sm"
                                            value={newTask.assigned_to}
                                            onChange={e => setNewTask({ ...newTask, assigned_to: e.target.value })}
                                        >
                                            <option value="">Leave Unassigned</option>
                                            {teamMembers.map(m => (
                                                <option key={m.id} value={m.id}>{m.first_name} {m.last_name} (@{m.username})</option>
                                            ))}
                                        </select>
                                    </div>
                                </div>
                                <DialogFooter>
                                    <Button variant="outline" onClick={() => setIsCreateModalOpen(false)}>Cancel</Button>
                                    <Button onClick={handleCreateCustomTask} disabled={!newTask.project || !newTask.comments}>Create Task</Button>
                                </DialogFooter>
                            </DialogContent>
                        </Dialog>
                    )}
                    <Button variant="outline" className="h-11 w-11 p-0 rounded-full" onClick={fetchTasks}>
                        <Clock className="h-5 w-5" />
                    </Button>
                </div>
            </header>

            {/* Navigation Tabs */}
            <div className="flex border-b overflow-x-auto no-scrollbar">
                {[
                    { id: 'my_tasks', label: 'My Responsibilities', icon: FileText },
                    { id: 'department', label: 'Departmental Scope', icon: UserPlus, hide: !user?.is_hod && !user?.is_superuser },
                    { id: 'project_owner', label: 'Project Control', icon: Check, hide: !user?.is_owner && !user?.is_superuser },
                    { id: 'all_tasks', label: 'Master Registry', icon: MoreHorizontal, hide: !user?.is_superuser }
                ].filter(t => !t.hide).map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id as any)}
                        className={`flex items-center gap-2 px-6 py-4 text-sm font-bold border-b-2 transition-all whitespace-nowrap ${activeTab === tab.id
                            ? 'border-primary text-primary'
                            : 'border-transparent text-muted-foreground hover:text-foreground hover:border-muted-foreground/30'
                            }`}
                    >
                        <tab.icon className="h-4 w-4" />
                        {tab.label}
                    </button>
                ))}
            </div>

            {/* Bulk Action Bar - Sticky Bottom */}
            {selectedTasks.length > 0 && (
                <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 bg-foreground text-background px-6 py-3 rounded-full shadow-2xl flex items-center gap-4 animate-in slide-in-from-bottom-4 duration-300">
                    <span className="font-bold whitespace-nowrap">{selectedTasks.length} selected</span>
                    <div className="h-4 w-[1px] bg-background/20" />

                    {/* HOD Bulk Assign */}
                    {(activeTab === 'department' || user?.is_hod) && (
                        <div className="flex items-center gap-2">
                            <select
                                className="h-8 rounded bg-background/10 border-background/20 text-background text-xs px-2"
                                value={bulkAssignee}
                                onChange={e => setBulkAssignee(e.target.value)}
                            >
                                <option value="" className="text-foreground">Assign Member...</option>
                                {teamMembers.map(m => (
                                    <option key={m.id} value={m.id} className="text-foreground">{m.first_name} {m.last_name}</option>
                                ))}
                            </select>
                            <Button size="sm" variant="secondary" className="h-8" onClick={handleBulkAssignMember} disabled={!bulkAssignee}>
                                Assign
                            </Button>
                        </div>
                    )}

                    {/* Owner Bulk Department Move */}
                    {(activeTab === 'project_owner' || user?.is_owner) && (
                        <div className="flex items-center gap-2">
                            <div className="h-4 w-[1px] bg-background/20" />
                            <select
                                className="h-8 rounded bg-background/10 border-background/20 text-background text-xs px-2"
                                value={bulkDepartment}
                                onChange={e => setBulkDepartment(e.target.value)}
                            >
                                <option value="" className="text-foreground">Move Dept...</option>
                                {departments.map(d => (
                                    <option key={d.id} value={d.id} className="text-foreground">{d.name}</option>
                                ))}
                            </select>
                            <Button size="sm" variant="secondary" className="h-8" onClick={handleBulkAssignDept} disabled={!bulkDepartment}>
                                Move
                            </Button>
                        </div>
                    )}

                    <Button size="icon" variant="ghost" className="h-8 w-8 ml-2 rounded-full hover:bg-white/20 text-white" onClick={() => setSelectedTasks([])}>
                        <Plus className="h-4 w-4 rotate-45" />
                    </Button>
                </div>
            )}

            <div className="grid gap-4">
                {/* Select All Header (Optional, or just put checking in rows) */}
                {(activeTab === 'department' || activeTab === 'project_owner') && tasks.length > 0 && (
                    <div className="flex items-center gap-2 px-1">
                        <input
                            type="checkbox"
                            className="h-4 w-4 rounded border-gray-300"
                            checked={selectedTasks.length === tasks.length && tasks.length > 0}
                            onChange={toggleSelectAll}
                        />
                        <span className="text-sm font-bold text-muted-foreground uppercase tracking-wider">Select All Tasks</span>
                    </div>
                )}

                {loading ? (
                    <>
                        <TaskCardSkeleton />
                        <TaskCardSkeleton />
                    </>
                ) : tasks.length === 0 ? (
                    <div className="py-20 text-center bg-muted/20 rounded-2xl border-2 border-dashed border-muted">
                        <FileText className="h-12 w-12 text-muted-foreground/50 mx-auto mb-4" />
                        <h3 className="text-lg font-bold">No active tasks found</h3>
                    </div>
                ) : (
                    tasks.map(task => (
                        <Card key={task.id} className={`group border-primary/5 hover:border-primary/20 transition-all shadow-sm ${expandedTask === task.id ? 'ring-2 ring-primary/20 shadow-lg' : ''} ${selectedTasks.includes(task.id) ? 'bg-primary/5 border-primary/30' : ''}`}>
                            <div className="p-6">
                                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                                    {/* Checkbox for Bulk Actions */}
                                    <div className="flex items-start gap-4 flex-1">
                                        {(activeTab === 'department' || activeTab === 'project_owner') && (
                                            <input
                                                type="checkbox"
                                                className="mt-1.5 h-4 w-4 rounded border-gray-300 cursor-pointer"
                                                checked={selectedTasks.includes(task.id)}
                                                onChange={() => toggleSelect(task.id)}
                                            />
                                        )}

                                        <div className="space-y-1">
                                            <div className="flex items-center gap-3">
                                                <span className="text-[10px] font-black uppercase tracking-[0.2em] px-2 py-0.5 rounded bg-foreground text-background">
                                                    {task.project_name}
                                                </span>
                                                <span className={`text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded border ${getStatusColor(task.status)}`}>
                                                    {task.status}
                                                </span>
                                                {task.status === 'RETURNED' && (
                                                    <span className="text-[10px] font-bold text-destructive animate-pulse">ACTION REQUIRED</span>
                                                )}
                                            </div>
                                            <h3 className="text-lg font-extrabold mt-2 hover:text-primary transition-colors cursor-pointer">
                                                <Link to={`/dms/tasks/${task.id}`}>
                                                    {task.p6_activity_name || task.workflow_step_details?.action_description || "Custom Assignment"}
                                                </Link>
                                            </h3>
                                            <p className="text-sm text-muted-foreground">
                                                {task.p6_activity_name ? `Workflow Step: ${task.workflow_step_details?.action_description}` : task.workflow_step_details?.sequence_id ? `Workflow ID: ${task.workflow_step_details.sequence_id}` : "Manual Control"}
                                            </p>
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-4">
                                        <div className="text-right hidden sm:block">
                                            <p className="text-xs font-bold text-muted-foreground uppercase tracking-widest">Created</p>
                                            <p className="text-sm font-medium">{new Date(task.created_at).toLocaleDateString()}</p>
                                        </div>
                                        <div className="flex gap-2">
                                            <Button variant="outline" size="sm" className="font-bold border-2" asChild>
                                                <Link to={`/dms/tasks/${task.id}`}>Workspace</Link>
                                            </Button>
                                            <Button
                                                variant={expandedTask === task.id ? "default" : "outline"}
                                                size="sm"
                                                className="font-bold border-2"
                                                onClick={() => handleExpand(task)}
                                            >
                                                Quick Actions <ChevronDown className={`ml-2 h-4 w-4 transition-transform ${expandedTask === task.id ? 'rotate-180' : ''}`} />
                                            </Button>
                                        </div>
                                    </div>
                                </div>

                                {task.comments && (
                                    <div className="mt-4 p-3 bg-muted/30 rounded-lg border italic text-sm text-muted-foreground">
                                        "{task.comments}"
                                    </div>
                                )}

                                {task.assigned_to_details && (
                                    <div className="mt-4 flex items-center gap-2">
                                        <div className="h-6 w-6 rounded-full bg-primary/10 flex items-center justify-center text-[10px] font-bold text-primary">
                                            {task.assigned_to_details.first_name[0]}{task.assigned_to_details.last_name[0]}
                                        </div>
                                        <span className="text-xs font-bold text-foreground/80">
                                            Assigned to {task.assigned_to_details.first_name} {task.assigned_to_details.last_name}
                                        </span>
                                    </div>
                                )}

                                {/* Action Area */}
                                {expandedTask === task.id && (
                                    <div className="mt-6 pt-6 border-t animate-in fade-in slide-in-from-top-2 duration-300">
                                        <div className="grid gap-6">
                                            {/* Reference Documents */}
                                            {task.related_documents && task.related_documents.length > 0 && (
                                                <div className="grid gap-2">
                                                    <Label className="text-xs font-bold text-muted-foreground uppercase tracking-widest">Reference Documents (Received)</Label>
                                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                                        {task.related_documents.map(doc => (
                                                            <a
                                                                key={doc.id}
                                                                href={doc.file}
                                                                target="_blank"
                                                                rel="noopener noreferrer"
                                                                className="flex items-center gap-3 p-3 rounded-lg border bg-blue-50/30 border-blue-100 hover:bg-blue-50 transition-colors group/doc"
                                                            >
                                                                <FileText className="h-5 w-5 text-blue-600" />
                                                                <div className="overflow-hidden">
                                                                    <p className="text-xs font-bold truncate">{doc.document_type}</p>
                                                                    <p className="text-[10px] text-muted-foreground">Uploaded by {doc.uploaded_by.first_name}</p>
                                                                </div>
                                                                <Download className="h-3 w-3 ml-auto opacity-0 group-hover/doc:opacity-100 transition-opacity" />
                                                            </a>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}

                                            <div className="grid gap-2">
                                                <Label className="text-xs font-bold text-muted-foreground">Action Comments / Feedback</Label>
                                                <Input
                                                    placeholder={activeTab === 'department' ? "Add note or reject reason..." : "Describe the outcome..."}
                                                    value={actionComment}
                                                    onChange={e => setActionComment(e.target.value)}
                                                />
                                            </div>

                                            <div className="flex flex-wrap items-end justify-between gap-4">
                                                {/* Role-Specific Actions */}
                                                {(activeTab === 'department' || activeTab === 'project_owner' || activeTab === 'all_tasks') ? (
                                                    <div className="flex flex-wrap gap-2">
                                                        <div className="grid gap-1">
                                                            <span className="text-[10px] font-bold uppercase text-muted-foreground">Assignee</span>
                                                            <select
                                                                className="h-9 w-48 rounded-md border border-input px-3 text-xs bg-background"
                                                                value={assigneeId}
                                                                onChange={e => setAssigneeId(e.target.value)}
                                                            >
                                                                <option value="">Select Member</option>
                                                                {teamMembers.map(m => (
                                                                    <option key={m.id} value={m.id}>{m.first_name} {m.last_name}</option>
                                                                ))}
                                                            </select>
                                                        </div>
                                                        {hasPermission('approve_tasks', task.project) && (
                                                            <>
                                                                <Button size="sm" variant="outline" className="h-9 rounded-md border-2 font-bold" onClick={() => handleAction(task.id, 'ASSIGN')} disabled={!assigneeId}>
                                                                    <UserPlus className="mr-2 h-4 w-4" /> Re-assign
                                                                </Button>

                                                                {/* HOD Return to Owner */}
                                                                <Button size="sm" variant="outline" className="h-9 rounded-md border-2 border-orange-200 text-orange-700 bg-orange-50 hover:bg-orange-100 font-bold" onClick={() => handleAction(task.id, 'RETURN')}>
                                                                    Return to Owner
                                                                </Button>

                                                                <div className="w-[2px] bg-muted h-9 mx-2 hidden sm:block" />
                                                                <Button size="sm" className="h-9 rounded-md font-bold bg-green-600 hover:bg-green-700 shadow-lg shadow-green-600/20" onClick={() => handleAction(task.id, 'APPROVE')}>
                                                                    <Check className="mr-2 h-4 w-4" /> Final Approve
                                                                </Button>
                                                                <Button size="sm" variant="destructive" className="h-9 rounded-md font-bold shadow-lg shadow-red-600/20" onClick={() => handleAction(task.id, 'REJECT')}>
                                                                    Reject
                                                                </Button>
                                                            </>
                                                        )}
                                                    </div>
                                                ) : (
                                                    <div className="flex flex-wrap items-end gap-3 w-full">
                                                        {/* Team Member View */}
                                                        <div className="grid gap-1 flex-1 min-w-[200px]">
                                                            <span className="text-[10px] font-bold uppercase text-muted-foreground">Document Submission</span>
                                                            <div className="relative group/file">
                                                                <Input type="file" onChange={e => setSelectedFile(e.target.files?.[0] || null)} className="h-9 pr-20 cursor-pointer text-xs" />
                                                                <Button
                                                                    size="sm" variant="link"
                                                                    className="absolute right-1 top-0 h-9 text-xs font-bold opacity-0 group-hover/file:opacity-100 transition-opacity"
                                                                    onClick={() => handleUpload(task.id)} disabled={!selectedFile}
                                                                >
                                                                    <Upload className="h-3 w-3 mr-1" /> Upload
                                                                </Button>
                                                            </div>
                                                        </div>
                                                        <div className="flex gap-2">
                                                            {hasPermission('submit_tasks') && (
                                                                <>
                                                                    <Button size="sm" variant="outline" className="h-9 font-bold border-2" onClick={() => handleAction(task.id, 'START')} disabled={task.status === 'IN_PROGRESS'}>
                                                                        <Play className="mr-2 h-4 w-4" /> Mark as Started
                                                                    </Button>
                                                                    <Button size="sm" className="h-9 font-bold shadow-lg shadow-primary/20" onClick={() => handleAction(task.id, 'SUBMIT')}>
                                                                        Submit for Review
                                                                    </Button>
                                                                </>
                                                            )}
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </Card>
                    ))
                )}
            </div>
        </div>
    );
}
