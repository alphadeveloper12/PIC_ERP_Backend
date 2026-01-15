import { useEffect, useState } from 'react';
import api from '@/services/api';
import {
    Shield,
    Save,
    RefreshCw,
    Search,
    ChevronRight,
    Settings,
    Layers,
    Lock,
    Info,
    CheckCircle,
    Building2
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
    DialogFooter,
} from '@/components/ui/dialog';
import { toast } from 'sonner';

interface PermissionDetail {
    id: number;
    code: string;
    description: string;
    category: 'GENERAL' | 'DEPARTMENTAL' | 'ADMINISTRATIVE';
}

interface Project {
    id: number;
    name: string;
    code: string;
}

interface AccessPolicy {
    id: number;
    department: number;
    department_name: string;
    department_code: string;
    role: string;
    permissions: string[];
}

// Global Permission Dictionary for Better UI/UX
const PERMISSION_GUIDE: Record<string, { name: string; desc: string; category: 'GENERAL' | 'DEPARTMENTAL' | 'ADMINISTRATIVE' }> = {
    // GENERAL
    'view_dashboard': {
        name: 'Access Dashboard',
        desc: 'Allows viewing of the main project dashboard and summary statistics.',
        category: 'GENERAL'
    },
    'view_tasks': {
        name: 'View Tasks',
        desc: 'Allows viewing of tasks within the assigned scope/department.',
        category: 'GENERAL'
    },
    'view_team': {
        name: 'View Team List',
        desc: 'Visibility of other members in the project team.',
        category: 'GENERAL'
    },
    'view_planning': {
        name: 'View Planning',
        desc: 'Read-only access to Primavera sheets and activity schedules.',
        category: 'GENERAL'
    },

    // DEPARTMENTAL
    'submit_tasks': {
        name: 'Execute & Submit',
        desc: 'Allows starting and submitting tasks, and uploading required evidence/documents.',
        category: 'DEPARTMENTAL'
    },
    'approve_tasks': {
        name: 'Approve / Reject',
        desc: 'Critical authority to finalize or reject department workflow steps.',
        category: 'DEPARTMENTAL'
    },
    'manage_team': {
        name: 'Team Lead Authority',
        desc: 'Allows assigning tasks specifically to department members and managing internal roles.',
        category: 'DEPARTMENTAL'
    },
    'view_procurement': {
        name: 'Procurement Visibility',
        desc: 'Access to read-only procurement logs and material statuses.',
        category: 'DEPARTMENTAL'
    },
    'manage_procurement': {
        name: 'Procurement Control',
        desc: 'Full authority to create and manage the procurement cycle and vendor interactions.',
        category: 'DEPARTMENTAL'
    },
    'view_hr': {
        name: 'HR Visibility',
        desc: 'Access to departmental personnel data and attendance records.',
        category: 'DEPARTMENTAL'
    },
    'manage_hr': {
        name: 'HR Administration',
        desc: 'Authority to manage HR records and department staffing levels.',
        category: 'DEPARTMENTAL'
    },

    // ADMINISTRATIVE
    'manage_projects': {
        name: 'Project Settings',
        desc: 'High-level project control. Access to settings, phases, and these permissions.',
        category: 'ADMINISTRATIVE'
    },
    'manage_planning': {
        name: 'Planning Control',
        desc: 'Full authority to import and link Primavera schedules with the ERP.',
        category: 'ADMINISTRATIVE'
    },
    'manage_users': {
        name: 'User Management',
        desc: 'Global authority to manage system user accounts and cross-project roles.',
        category: 'ADMINISTRATIVE'
    },
    'superuser': {
        name: 'System Admin (Global)',
        desc: 'Unrestricted "God Mode" bypass of all security checks across the entire system.',
        category: 'ADMINISTRATIVE'
    }
};

export default function PermissionsManager() {
    const [projects, setProjects] = useState<Project[]>([]);
    const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
    const [policies, setPolicies] = useState<AccessPolicy[]>([]);
    const [availablePermissions, setAvailablePermissions] = useState<PermissionDetail[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [editingId, setEditingId] = useState<number | null>(null);
    const [editPerms, setEditPerms] = useState<string[]>([]);
    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const [activeTab, setActiveTab] = useState<'GENERAL' | 'DEPARTMENTAL' | 'ADMINISTRATIVE'>('GENERAL');
    const [selectedPolicy, setSelectedPolicy] = useState<AccessPolicy | null>(null);

    const fetchProjects = async () => {
        try {
            const res = await api.get('/api/projects/');
            const projectsData = Array.isArray(res.data) ? res.data : res.data.data || [];
            setProjects(projectsData);
            if (projectsData.length > 0 && !selectedProjectId) {
                setSelectedProjectId(projectsData[0].id);
            }
        } catch (error) {
            toast.error('Failed to load projects');
        }
    };

    const fetchPolicies = async () => {
        if (!selectedProjectId) return;
        try {
            setLoading(true);
            const [policiesRes, permsRes] = await Promise.all([
                api.get(`/dms/access-policies/?project_id=${selectedProjectId}`),
                api.get('/core/permissions/')
            ]);
            setPolicies(policiesRes.data);
            const permData = Array.isArray(permsRes.data) ? permsRes.data : permsRes.data.data || [];
            setAvailablePermissions(permData);
        } catch (error) {
            toast.error('Failed to load permissions for this project');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchProjects();
    }, []);

    useEffect(() => {
        fetchPolicies();
    }, [selectedProjectId]);

    const handleSave = async (id: number) => {
        try {
            await api.patch(`/dms/access-policies/${id}/`, {
                permissions: editPerms
            });
            toast.success('Permissions updated successfully');
            setIsDialogOpen(false);
            setEditingId(null);
            fetchPolicies();
        } catch (error) {
            toast.error('Failed to update permissions');
        }
    };

    const startEditing = (policy: AccessPolicy) => {
        setEditingId(policy.id);
        setEditPerms(policy.permissions);
        setSelectedPolicy(policy);
        setIsDialogOpen(true);
    };

    const togglePermission = (code: string) => {
        setEditPerms(prev =>
            prev.includes(code) ? prev.filter(p => p !== code) : [...prev, code]
        );
    };

    const filteredPolicies = policies.filter(p =>
        p.department_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.role.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const groupedDefinitions = {
        GENERAL: Object.entries(PERMISSION_GUIDE).filter(([_, def]) => def.category === 'GENERAL'),
        DEPARTMENTAL: Object.entries(PERMISSION_GUIDE).filter(([_, def]) => def.category === 'DEPARTMENTAL'),
        ADMINISTRATIVE: Object.entries(PERMISSION_GUIDE).filter(([_, def]) => def.category === 'ADMINISTRATIVE'),
    };

    return (
        <div className="space-y-6 max-w-7xl mx-auto px-4 sm:px-6">
            {/* Header with Project Selector */}
            <div className="flex flex-col xl:flex-row justify-between items-start xl:items-center gap-6 bg-white p-8 rounded-3xl shadow-sm border border-primary/5">
                <div className="space-y-1">
                    <h1 className="text-4xl font-black tracking-tight text-foreground flex items-center gap-4">
                        <div className="bg-primary/10 p-2 rounded-2xl text-primary">
                            <Shield className="h-10 w-10" />
                        </div>
                        Access & Permissions
                    </h1>
                    <p className="text-muted-foreground font-medium text-lg italic pl-16">
                        Project-specific security policies for every department.
                    </p>
                </div>

                <div className="flex flex-wrap items-center gap-4 w-full xl:w-auto">
                    <div className="flex-1 min-w-[300px] xl:w-80 group">
                        <Label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground/60 mb-2 block ml-2">Active Project Context</Label>
                        <div className="relative">
                            <Building2 className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-primary/40 group-hover:text-primary transition-colors" />
                            <select
                                className="w-full h-14 pl-12 pr-4 bg-primary/5 border-2 border-transparent focus:border-primary rounded-2xl font-bold text-lg appearance-none cursor-pointer transition-all"
                                value={selectedProjectId || ''}
                                onChange={e => setSelectedProjectId(Number(e.target.value))}
                            >
                                {projects.map(prj => (
                                    <option key={prj.id} value={prj.id}>[{prj.code}] {prj.name}</option>
                                ))}
                            </select>
                        </div>
                    </div>
                    <Button variant="outline" onClick={fetchPolicies} disabled={loading} className="rounded-2xl border-2 font-black h-14 px-8 mt-6">
                        <RefreshCw className={`mr-3 h-5 w-5 ${loading ? 'animate-spin' : ''}`} />
                        Reload
                    </Button>
                </div>
            </div>

            <Card className="p-8 border-none shadow-2xl shadow-primary/5 rounded-[2.5rem] bg-white/50 backdrop-blur-xl">
                {/* Search & Statistics */}
                <div className="flex flex-col md:flex-row items-center gap-6 mb-10">
                    <div className="relative flex-1 group">
                        <Search className="absolute left-6 top-1/2 -translate-y-1/2 h-6 w-6 text-muted-foreground/50 group-focus-within:text-primary transition-colors" />
                        <Input
                            placeholder="Search roles or departments..."
                            className="pl-16 h-16 bg-white border-2 border-primary/5 rounded-2xl text-xl font-semibold shadow-inner focus-visible:ring-primary/10"
                            value={searchQuery}
                            onChange={e => setSearchQuery(e.target.value)}
                        />
                    </div>
                    <div className="hidden lg:flex items-center gap-8 px-8 py-5 bg-white rounded-2xl border border-primary/5 shadow-sm">
                        <div className="text-center">
                            <div className="text-2xl font-black text-primary">{policies.length}</div>
                            <div className="text-[10px] font-black uppercase text-muted-foreground">Policies</div>
                        </div>
                        <div className="w-[1px] h-8 bg-muted" />
                        <div className="text-center">
                            <div className="text-2xl font-black text-primary">{availablePermissions.length}</div>
                            <div className="text-[10px] font-black uppercase text-muted-foreground">Capabilities</div>
                        </div>
                    </div>
                </div>

                {/* Policy Table */}
                <div className="overflow-x-auto -mx-2">
                    <table className="w-full text-left border-separate border-spacing-y-4">
                        <thead>
                            <tr className="text-[10px] font-black uppercase tracking-[0.4em] text-muted-foreground/40">
                                <th className="px-8 py-2">Department</th>
                                <th className="px-8 py-2">Authority Role</th>
                                <th className="px-8 py-2">Active Privileges</th>
                                <th className="px-8 py-2 text-right">Operations</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                [1, 2, 3].map(i => (
                                    <tr key={i} className="animate-pulse">
                                        <td colSpan={4} className="h-24 bg-muted/10 rounded-3xl"></td>
                                    </tr>
                                ))
                            ) : filteredPolicies.map(policy => (
                                <tr key={policy.id} className="group bg-white rounded-3xl transition-all duration-300 hover:shadow-xl hover:shadow-primary/5 border border-primary/5">
                                    <td className="px-8 py-6 rounded-l-3xl">
                                        <div className="flex items-center gap-4">
                                            <div className="h-12 w-12 rounded-xl bg-primary/5 flex items-center justify-center font-black text-primary text-xs shadow-inner">
                                                {policy.department_code}
                                            </div>
                                            <span className="font-bold text-lg text-foreground/80">{policy.department_name}</span>
                                        </div>
                                    </td>
                                    <td className="px-8 py-6">
                                        <div className={`px-4 py-2 rounded-xl text-[10px] font-black tracking-widest uppercase border-2 inline-flex items-center gap-2 ${policy.role === 'HOD' ? 'bg-amber-50 border-amber-200 text-amber-700' :
                                            policy.role === 'ADMIN' ? 'bg-sky-50 border-sky-200 text-sky-700' : 'bg-slate-50 border-slate-200 text-slate-700'
                                            }`}>
                                            {policy.role === 'HOD' && <Settings className="h-3 w-3" />}
                                            {policy.role === 'HOD' ? 'Head of Dept' : policy.role === 'ADMIN' ? 'Site Admin' : 'Officer'}
                                        </div>
                                    </td>
                                    <td className="px-8 py-6">
                                        <div className="space-y-2 max-w-sm">
                                            {['GENERAL', 'DEPARTMENTAL', 'ADMINISTRATIVE'].map(cat => {
                                                const catPerms = policy.permissions.filter(code => PERMISSION_GUIDE[code]?.category === cat);
                                                if (catPerms.length === 0) return null;
                                                return (
                                                    <div key={cat} className="flex flex-wrap gap-1.5 items-center">
                                                        <div className={`h-1.5 w-1.5 rounded-full shrink-0 ${cat === 'GENERAL' ? 'bg-blue-500' : cat === 'ADMINISTRATIVE' ? 'bg-purple-500' : 'bg-orange-500'}`} />
                                                        <div className="flex flex-wrap gap-1">
                                                            {catPerms.map(code => (
                                                                <span
                                                                    key={code}
                                                                    title={`${PERMISSION_GUIDE[code]?.name}: ${PERMISSION_GUIDE[code]?.desc}`}
                                                                    className="text-[9px] font-bold bg-muted/30 px-2 py-0.5 rounded-md text-muted-foreground cursor-help hover:bg-muted transition-colors whitespace-nowrap"
                                                                >
                                                                    {PERMISSION_GUIDE[code]?.name || code}
                                                                </span>
                                                            ))}
                                                        </div>
                                                    </div>
                                                );
                                            })}
                                            {policy.permissions.length === 0 && <span className="text-[10px] italic text-muted-foreground/50">No privileges</span>}
                                        </div>
                                    </td>
                                    <td className="px-8 py-6 rounded-r-3xl text-right">
                                        <Button
                                            variant="ghost"
                                            className="rounded-2xl font-black text-xs h-11 px-6 hover:bg-primary/5 text-primary border-2 border-transparent hover:border-primary/10 transition-all"
                                            onClick={() => startEditing(policy)}
                                        >
                                            <Settings className="h-4 w-4 mr-2" />
                                            Configure
                                        </Button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </Card>

            {/* Configuration Modal */}
            <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                <DialogContent className="max-w-4xl rounded-[2.5rem] p-0 overflow-hidden border-none shadow-2xl">
                    <DialogHeader className="p-8 pb-4 bg-primary/5">
                        <div className="flex items-center gap-4">
                            <div className="bg-primary/10 p-3 rounded-2xl text-primary">
                                <Shield className="h-8 w-8" />
                            </div>
                            <div>
                                <DialogTitle className="text-2xl font-black tracking-tight">
                                    {selectedPolicy?.department_name} - {selectedPolicy?.role}
                                </DialogTitle>
                                <DialogDescription className="text-sm font-medium text-muted-foreground italic">
                                    Grant or revoke specific project authorities.
                                </DialogDescription>
                            </div>
                        </div>
                    </DialogHeader>

                    <div className="p-8 pt-4 space-y-8">
                        {/* Tab Headers */}
                        <div className="flex gap-2 p-1.5 bg-muted/20 rounded-2xl border border-primary/5">
                            {(['GENERAL', 'DEPARTMENTAL', 'ADMINISTRATIVE'] as const).map(cat => (
                                <button
                                    key={cat}
                                    onClick={() => setActiveTab(cat)}
                                    className={`flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-xl text-xs font-black transition-all ${activeTab === cat
                                        ? 'bg-white shadow-sm text-primary scale-100 border border-primary/10'
                                        : 'text-muted-foreground/60 hover:text-muted-foreground hover:bg-white/50'
                                        }`}
                                >
                                    {cat === 'GENERAL' ? <Layers className="h-4 w-4" /> :
                                        cat === 'ADMINISTRATIVE' ? <Lock className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                                    {cat}
                                </button>
                            ))}
                        </div>

                        {/* Tab Content */}
                        <div className="min-h-[300px]">
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
                                {groupedDefinitions[activeTab].map(([code, def]) => (
                                    <button
                                        key={code}
                                        onClick={() => togglePermission(code)}
                                        className={`p-5 rounded-2xl text-left transition-all duration-200 border-2 group shadow-sm ${editPerms.includes(code)
                                            ? 'bg-primary border-primary text-white scale-[1.02] shadow-primary/20'
                                            : 'bg-white border-primary/5 text-muted-foreground hover:border-primary/20 hover:scale-[1.01]'
                                            }`}
                                    >
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="font-black text-sm">{def.name}</span>
                                            {editPerms.includes(code) ? (
                                                <CheckCircle className="h-5 w-5 text-white" />
                                            ) : (
                                                <div className="h-5 w-5 rounded-full border-2 border-primary/10 group-hover:border-primary/30 transition-colors" />
                                            )}
                                        </div>
                                        <p className={`text-[11px] leading-relaxed font-medium ${editPerms.includes(code) ? 'text-primary-foreground/80' : 'text-muted-foreground'}`}>
                                            {def.desc}
                                        </p>
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>

                    <DialogFooter className="p-8 bg-muted/5 border-t border-primary/5 flex items-center justify-between sm:justify-between">
                        <div className="text-[10px] font-black uppercase tracking-widest text-muted-foreground/40 hidden sm:block">
                            {editPerms.length} Privileges Selected
                        </div>
                        <div className="flex gap-3 w-full sm:w-auto">
                            <Button variant="ghost" className="flex-1 sm:flex-none font-black text-xs rounded-2xl px-8 h-12" onClick={() => setIsDialogOpen(false)}>
                                Cancel
                            </Button>
                            <Button className="flex-1 sm:flex-none font-black text-xs rounded-2xl px-12 h-12 shadow-xl shadow-primary/20" onClick={() => editingId && handleSave(editingId)}>
                                <Save className="h-4 w-4 mr-2" /> Save Configuration
                            </Button>
                        </div>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Legend & Guide Section */}
            <div className="bg-muted/10 rounded-[2.5rem] p-10 border-2 border-primary/5">
                <div className="flex items-center gap-4 mb-8">
                    <div className="h-10 w-10 rounded-xl bg-white flex items-center justify-center border-2 border-primary/10 shadow-sm">
                        <Info className="h-5 w-5 text-primary" />
                    </div>
                    <h3 className="text-2xl font-black tracking-tight">Understanding User Roles</h3>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    <div className="space-y-4">
                        <div className="h-8 shadow-sm px-4 bg-amber-50 text-amber-900 flex items-center justify-center rounded-xl text-[10px] font-black uppercase tracking-widest border border-amber-200">Head of Department</div>
                        <p className="text-sm text-muted-foreground leading-relaxed font-medium">Strategic managers. Usually granted <span className="text-amber-700 font-bold">Approve/Reject</span> rights and <span className="text-amber-700 font-bold">Manage Team</span> permissions. They possess full oversight of their department's workflow stages.</p>
                    </div>
                    <div className="space-y-4">
                        <div className="h-8 shadow-sm px-4 bg-slate-50 text-slate-900 flex items-center justify-center rounded-xl text-[10px] font-black uppercase tracking-widest border border-slate-200">Officer / Staff</div>
                        <p className="text-sm text-muted-foreground leading-relaxed font-medium">Daily executors. Primarily assigned <span className="text-primary font-bold">Execute Tasks</span> and <span className="text-primary font-bold">View Dashboard</span>. They can start tasks, upload progress, and submit for review.</p>
                    </div>
                    <div className="space-y-4">
                        <div className="h-8 shadow-sm px-4 bg-sky-50 text-sky-900 flex items-center justify-center rounded-xl text-[10px] font-black uppercase tracking-widest border border-sky-200">Project Admin</div>
                        <p className="text-sm text-muted-foreground leading-relaxed font-medium">Site-wide support. Often granted <span className="text-sky-700 font-bold">Manage Team</span> and <span className="text-sky-700 font-bold">View Dashboard</span> for cross-departmental coordination without workflow finalization rights.</p>
                    </div>
                </div>
            </div>
        </div>
    );
}
