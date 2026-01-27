import { useState, useEffect } from 'react';
import api from '@/services/api';
import { useAuthStore } from '@/hooks/useAuthStore';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow
} from '@/components/ui/table';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger
} from '@/components/ui/dialog';
import {
    Search,
    Plus,
    ChevronLeft,
    ChevronRight,
    Filter,
    Upload,
    Database,
    History,
    FileSpreadsheet,
    AlertCircle,
    Info,
    Clock
} from 'lucide-react';
import { toast } from 'sonner';
import { Loading } from '@/components/Loading';

interface P6Activity {
    id: number;
    activity_id: string;
    activity_name: string;
    erc_code: string;
    original_duration: number;
    early_start: string;
    early_finish: string;
    late_start: string;
    late_finish: string;
    actual_start: string;
    actual_finish: string;
    budgeted_total_cost: string;
    primavera_sheet: number;
    status: string;
}

interface PrimaveraSheet {
    id: number;
    name: string;
    uploaded_at: string;
    subphase_name?: string;
    project_name?: string;
}

interface Project {
    id: number;
    name: string;
}

interface SubPhase {
    id: number;
    name: string;
}

export default function PlanningHub() {
    const { user } = useAuthStore();
    const [activeTab, setActiveTab] = useState<'activities' | 'uploads'>('activities');
    const [loading, setLoading] = useState(false);

    // Activities State
    const [activities, setActivities] = useState<P6Activity[]>([]);
    const [totalActivities, setTotalActivities] = useState(0);
    const [page, setPage] = useState(1);
    const [search, setSearch] = useState('');
    const [selectedSheetFilter, setSelectedSheetFilter] = useState<string>('');
    const [sheets, setSheets] = useState<PrimaveraSheet[]>([]);
    const [editingActivity, setEditingActivity] = useState<Partial<P6Activity> | null>(null);
    const [isActivityModalOpen, setIsActivityModalOpen] = useState(false);

    // Upload State
    const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [projects, setProjects] = useState<Project[]>([]);
    const [selectedProject, setSelectedProject] = useState('');
    const [subphases, setSubphases] = useState<SubPhase[]>([]);
    const [selectedSubphase, setSelectedSubphase] = useState('');
    const [uploadName, setUploadName] = useState('');
    const [selectedFile, setSelectedFile] = useState<File | null>(null);

    // Subphase Creation State
    const [isCreatingSubphase, setIsCreatingSubphase] = useState(false);
    const [newSubphaseName, setNewSubphaseName] = useState('');

    const fetchMeta = async () => {
        try {
            const [sheetsRes, projectsRes] = await Promise.all([
                api.get('/planning/primavera-sheets/'),
                api.get('/api/projects/?mode=my_projects')
            ]);
            setSheets(sheetsRes.data);
            setProjects(projectsRes.data.data);
        } catch (e) {
            console.error(e);
        }
    };

    const fetchActivities = async () => {
        setLoading(true);
        try {
            let url = `/planning/p6-activities/?page=${page}&search=${search}`;
            if (selectedSheetFilter) url += `&primavera_sheet=${selectedSheetFilter}`;
            const res = await api.get(url);
            setActivities(res.data.results);
            setTotalActivities(res.data.count);
        } catch (e) {
            console.error(e);
            toast.error("Failed to load activities");
        } finally {
            setLoading(false);
        }
    };

    const fetchSubphases = async (projectId: string) => {
        if (!projectId) return;
        try {
            const res = await api.get(`/api/projects/subphase/list/?project_id=${projectId}`);
            setSubphases(res.data.data);
        } catch (e) {
            console.error(e);
        }
    };

    useEffect(() => {
        fetchMeta();
    }, []);

    useEffect(() => {
        if (activeTab === 'activities') {
            fetchActivities();
        }
    }, [page, search, selectedSheetFilter, activeTab]);

    useEffect(() => {
        if (selectedProject) {
            fetchSubphases(selectedProject);
        }
    }, [selectedProject]);

    const handleSaveActivity = async () => {
        try {
            if (editingActivity?.id) {
                await api.put(`/planning/p6-activities/${editingActivity.id}/`, editingActivity);
                toast.success("Activity updated");
            } else {
                await api.post('/planning/p6-activities/', editingActivity);
                toast.success("Activity created");
            }
            setIsActivityModalOpen(false);
            fetchActivities();
        } catch (e) {
            console.error(e);
            toast.error("Failed to save activity");
        }
    };

    const handleUpload = async () => {
        if (!selectedFile || !selectedSubphase) return;
        setUploading(true);
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('subphase_id', selectedSubphase);
        formData.append('name', uploadName || selectedFile.name);

        try {
            await api.post('/planning/primavera-sheets/import_data/', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            toast.success("Schedule imported successfully");
            setIsUploadModalOpen(false);
            fetchMeta(); // Refresh sheets list
            setActiveTab('activities');
        } catch (e) {
            console.error(e);
            toast.error("Upload failed");
        } finally {
            setUploading(false);
        }
    };

    const handleCreateSubphase = async () => {
        if (!newSubphaseName || !selectedProject) return;
        setIsCreatingSubphase(true);
        try {
            await api.post('/api/projects/subphase/create/', {
                name: newSubphaseName,
                project: selectedProject
            });
            toast.success("Sub-phase created");
            setNewSubphaseName('');
            fetchSubphases(selectedProject);
        } catch (e) {
            console.error(e);
            toast.error("Failed to create sub-phase");
        } finally {
            setIsCreatingSubphase(false);
        }
    };

    const canEdit = user?.is_superuser || user?.is_owner || user?.is_hod;

    return (
        <div className="space-y-8 max-w-[1600px] mx-auto pb-20">
            {uploading && <Loading fullPage message="Processing Schedule Data..." />}

            <header className="erp-header flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                <div className="space-y-1">
                    <h1 className="text-2xl font-black tracking-tight text-foreground">Planning Hub</h1>
                    <p className="text-sm font-bold text-muted-foreground italic">Manage project schedules and P6 activity synchronization.</p>
                </div>

                <div className="flex items-center gap-3">
                    {canEdit && (
                        <Dialog open={isUploadModalOpen} onOpenChange={setIsUploadModalOpen}>
                            <DialogTrigger asChild>
                                <Button className="h-11 px-6 shadow-lg shadow-primary/20 gap-2">
                                    <Upload className="h-4 w-4" /> Import P6 Schedule
                                </Button>
                            </DialogTrigger>
                            <DialogContent className="sm:max-w-[550px]">
                                <DialogHeader>
                                    <DialogTitle>Import Primavera Data</DialogTitle>
                                    <DialogDescription>Link your P6 schedule to a project sub-phase.</DialogDescription>
                                </DialogHeader>
                                <div className="grid gap-6 py-4">
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="space-y-2">
                                            <label className="text-xs font-bold uppercase text-muted-foreground">Target Project</label>
                                            <select
                                                className="w-full h-10 rounded-md border border-input bg-background px-3 text-sm"
                                                value={selectedProject}
                                                onChange={e => setSelectedProject(e.target.value)}
                                            >
                                                <option value="">Select Project</option>
                                                {projects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                                            </select>
                                        </div>
                                        <div className="space-y-2">
                                            <label className="text-xs font-bold uppercase text-muted-foreground">Select Sub-Phase</label>
                                            <select
                                                className="w-full h-10 rounded-md border border-input bg-background px-3 text-sm"
                                                value={selectedSubphase}
                                                onChange={e => setSelectedSubphase(e.target.value)}
                                                disabled={!selectedProject}
                                            >
                                                <option value="">Select Sub-Phase</option>
                                                {subphases.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                                            </select>
                                        </div>
                                    </div>

                                    {selectedProject && subphases.length === 0 && (
                                        <div className="p-4 rounded-lg bg-orange-50 border border-orange-200 flex flex-col gap-3">
                                            <div className="flex items-center gap-2 text-orange-700 text-sm font-semibold">
                                                <AlertCircle className="h-4 w-4" /> No sub-phases found
                                            </div>
                                            <div className="flex gap-2">
                                                <Input
                                                    placeholder="New Sub-Phase Name"
                                                    value={newSubphaseName}
                                                    onChange={e => setNewSubphaseName(e.target.value)}
                                                    className="h-8 text-xs bg-white"
                                                />
                                                <Button size="sm" onClick={handleCreateSubphase} disabled={isCreatingSubphase || !newSubphaseName}>
                                                    Initialize
                                                </Button>
                                            </div>
                                        </div>
                                    )}

                                    <div className="space-y-2">
                                        <label className="text-xs font-bold uppercase text-muted-foreground">Upload Sheet Name (Optional)</label>
                                        <Input
                                            placeholder="Standard Planning - Rev 0"
                                            value={uploadName}
                                            onChange={e => setUploadName(e.target.value)}
                                        />
                                    </div>

                                    <div className="space-y-4">
                                        <label className="text-xs font-bold uppercase text-muted-foreground">Select P6 Excel File</label>
                                        <div className="border-2 border-dashed rounded-xl p-8 text-center hover:border-primary/50 transition-colors cursor-pointer bg-muted/5 group">
                                            <input
                                                type="file"
                                                className="hidden"
                                                id="p6-upload"
                                                onChange={e => setSelectedFile(e.target.files?.[0] || null)}
                                            />
                                            <label htmlFor="p6-upload" className="cursor-pointer space-y-2 block">
                                                <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center mx-auto group-hover:scale-110 transition-transform">
                                                    <FileSpreadsheet className="h-6 w-6 text-primary" />
                                                </div>
                                                <div className="text-sm font-bold text-foreground">
                                                    {selectedFile ? selectedFile.name : "Click to select or drag file"}
                                                </div>
                                                <div className="text-xs text-muted-foreground italic">Supports .xlsx and .xls formats</div>
                                            </label>
                                        </div>
                                    </div>
                                </div>
                                <DialogFooter>
                                    <Button variant="outline" onClick={() => setIsUploadModalOpen(false)}>Cancel</Button>
                                    <Button
                                        onClick={handleUpload}
                                        disabled={!selectedFile || !selectedSubphase || uploading}
                                        className="min-w-[120px]"
                                    >
                                        {uploading ? "Processing..." : "Finish Import"}
                                    </Button>
                                </DialogFooter>
                            </DialogContent>
                        </Dialog>
                    )}
                </div>
            </header>

            {/* Hub Navigation */}
            <div className="flex border-b overflow-x-auto no-scrollbar">
                {[
                    { id: 'activities', label: 'Schedule Registry', icon: Database },
                    { id: 'uploads', label: 'Import History', icon: History }
                ].map(tab => (
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

            <div className="animate-in fade-in duration-500">
                {activeTab === 'activities' ? (
                    <Card className="erp-card bg-card border-none shadow-2xl shadow-primary/5 ring-1 ring-primary/5 overflow-hidden">
                        <CardHeader className="bg-muted/30 pb-6 border-b">
                            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                                <div className="space-y-1">
                                    <CardTitle className="text-2xl font-black flex items-center gap-2">
                                        <Database className="h-5 w-5 text-primary" />
                                        Activities Registry
                                    </CardTitle>
                                    <CardDescription>Master list of all P6 activities imported into the ERP.</CardDescription>
                                </div>
                                <div className="flex flex-col sm:flex-row items-center gap-4">
                                    <div className="relative w-full sm:w-[300px]">
                                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                        <Input
                                            placeholder="Search Activity ID or Name..."
                                            className="pl-10 h-10 shadow-sm border-primary/20"
                                            value={search}
                                            onChange={e => { setSearch(e.target.value); setPage(1); }}
                                        />
                                    </div>
                                    <div className="relative w-full sm:w-[250px]">
                                        <Filter className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                        <select
                                            className="w-full h-10 pl-10 pr-4 rounded-md border border-primary/20 bg-background text-sm font-medium shadow-sm appearance-none"
                                            value={selectedSheetFilter}
                                            onChange={e => { setSelectedSheetFilter(e.target.value); setPage(1); }}
                                        >
                                            <option value="">All Uploaded Sheets</option>
                                            {sheets.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                                        </select>
                                    </div>
                                    {canEdit && (
                                        <Button
                                            variant="outline"
                                            size="icon"
                                            className="h-10 w-10 border-primary/20"
                                            onClick={() => { setEditingActivity({}); setIsActivityModalOpen(true); }}
                                        >
                                            <Plus className="h-5 w-5" />
                                        </Button>
                                    )}
                                </div>
                            </div>
                        </CardHeader>
                        <CardContent className="p-0">
                            <div className="overflow-x-auto">
                                <Table>
                                    <TableHeader>
                                        <TableRow className="bg-muted/50 text-[10px] uppercase font-black tracking-widest text-muted-foreground/80">
                                            <TableHead className="w-[150px] pl-6">Activity ID</TableHead>
                                            <TableHead>Descriptor</TableHead>
                                            <TableHead className="w-[140px] text-blue-600">Early S/F</TableHead>
                                            <TableHead className="w-[140px] text-orange-600">Late S/F</TableHead>
                                            <TableHead className="w-[140px] text-green-600">Actual S/F</TableHead>
                                            <TableHead className="w-[120px] text-right pr-6">Budgeted Cost</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {loading ? (
                                            <TableRow>
                                                <TableCell colSpan={6} className="h-64">
                                                    <Loading message="Fetching activities registry..." />
                                                </TableCell>
                                            </TableRow>
                                        ) : activities.length === 0 ? (
                                            <TableRow>
                                                <TableCell colSpan={6} className="h-64 text-center">
                                                    <Info className="h-8 w-8 text-muted-foreground/30 mx-auto mb-2" />
                                                    <p className="text-muted-foreground font-medium">No schedule data matched your criteria.</p>
                                                </TableCell>
                                            </TableRow>
                                        ) : activities.map((act) => (
                                            <TableRow
                                                key={act.id}
                                                className="hover:bg-primary/5 transition-colors border-b border-primary/5 group"
                                            >
                                                <TableCell className="pl-6">
                                                    <span className="font-mono text-[11px] font-black text-primary px-2 py-1 rounded bg-primary/10 border border-primary/20 uppercase">
                                                        {act.activity_id}
                                                    </span>
                                                </TableCell>
                                                <TableCell className="py-4">
                                                    <div className="flex flex-col gap-1">
                                                        <span className="text-sm font-extrabold text-foreground group-hover:text-primary transition-colors">
                                                            {act.activity_name}
                                                        </span>
                                                        <span className="text-[10px] font-bold text-muted-foreground uppercase opacity-70">
                                                            {act.erc_code || 'Unlinked Item'}
                                                        </span>
                                                    </div>
                                                </TableCell>
                                                <TableCell className="text-[11px] text-blue-700/80 font-black">
                                                    <div className="flex flex-col bg-blue-50/50 p-2 rounded border border-blue-100/50 w-full">
                                                        <span>S: {act.early_start ? act.early_start.split('T')[0] : '---'}</span>
                                                        <span>F: {act.early_finish ? act.early_finish.split('T')[0] : '---'}</span>
                                                    </div>
                                                </TableCell>
                                                <TableCell className="text-[11px] text-orange-700/80 font-black">
                                                    <div className="flex flex-col bg-orange-50/50 p-2 rounded border border-orange-100/50 w-full">
                                                        <span>S: {act.late_start ? act.late_start.split('T')[0] : '---'}</span>
                                                        <span>F: {act.late_finish ? act.late_finish.split('T')[0] : '---'}</span>
                                                    </div>
                                                </TableCell>
                                                <TableCell className="text-[11px] text-green-700 font-black">
                                                    <div className="flex flex-col bg-green-50/50 p-2 rounded border border-green-100/50 w-full">
                                                        <span>S: {act.actual_start ? act.actual_start.split('T')[0] : '---'}</span>
                                                        <span>F: {act.actual_finish ? act.actual_finish.split('T')[0] : '---'}</span>
                                                    </div>
                                                </TableCell>
                                                <TableCell className="text-right pr-6 tabular-nums font-black text-foreground">
                                                    {act.budgeted_total_cost ? parseFloat(act.budgeted_total_cost).toLocaleString() : '0.00'}
                                                </TableCell>
                                            </TableRow>
                                        ))}
                                    </TableBody>
                                </Table>
                            </div>

                            {/* Pagination */}
                            <div className="flex items-center justify-between p-6 border-t bg-muted/20">
                                <div className="text-xs font-bold text-muted-foreground uppercase tracking-widest">
                                    Displaying <span className="text-foreground">{(page - 1) * 5 + 1}</span> to <span className="text-foreground">{Math.min(page * 5, totalActivities)}</span> of <span className="text-foreground">{totalActivities}</span>
                                </div>
                                <div className="flex gap-4">
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        className="h-9 px-4 font-black border-primary/20"
                                        disabled={page === 1}
                                        onClick={() => setPage(p => p - 1)}
                                    >
                                        <ChevronLeft className="h-4 w-4 mr-2" /> Prev
                                    </Button>
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        className="h-9 px-4 font-black border-primary/20"
                                        disabled={page * 5 >= totalActivities}
                                        onClick={() => setPage(p => p + 1)}
                                    >
                                        Next <ChevronRight className="h-4 w-4 ml-2" />
                                    </Button>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {sheets.length === 0 ? (
                            <div className="col-span-full py-32 text-center bg-white rounded-2xl border-2 border-dashed border-primary/10">
                                <History className="h-12 w-12 text-primary/20 mx-auto mb-4" />
                                <h3 className="text-xl font-black">No schedule history</h3>
                                <p className="text-muted-foreground">Import your first Primavera sheet to see it here.</p>
                            </div>
                        ) : sheets.map(sheet => (
                            <Card key={sheet.id} className="group hover:border-primary/50 transition-all shadow-sm hover:shadow-xl hover:shadow-primary/5">
                                <CardHeader className="pb-4">
                                    <div className="flex items-start justify-between">
                                        <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                                            <FileSpreadsheet className="h-5 w-5" />
                                        </div>
                                        <span className="text-[10px] font-black uppercase bg-green-100 text-green-700 px-2 py-0.5 rounded border border-green-200">
                                            Processed
                                        </span>
                                    </div>
                                    <CardTitle className="mt-4 text-lg font-black">{sheet.name}</CardTitle>
                                    <CardDescription className="text-xs font-bold uppercase tracking-widest text-muted-foreground/60">
                                        {sheet.subphase_name || "Historical Import"}
                                    </CardDescription>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
                                        <Clock className="h-3.5 w-3.5" />
                                        {new Date(sheet.uploaded_at).toLocaleString()}
                                    </div>
                                    <div className="flex items-center gap-2 text-xs font-black uppercase tracking-tighter text-foreground/80">
                                        <Database className="h-3.5 w-3.5" />
                                        Data linked to ERP Schedule
                                    </div>
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        className="w-full mt-2 font-black border-t rounded-none py-6 group-hover:bg-primary group-hover:text-white transition-all"
                                        onClick={() => { setSelectedSheetFilter(sheet.id.toString()); setActiveTab('activities'); }}
                                    >
                                        Inspect Activities <ChevronRight className="ml-2 h-4 w-4" />
                                    </Button>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                )}
            </div>

            {/* Hidden Add/Edit Activity Modal */}
            <Dialog open={isActivityModalOpen} onOpenChange={setIsActivityModalOpen}>
                <DialogContent className="max-w-2xl">
                    <DialogHeader>
                        <DialogTitle>{editingActivity?.id ? 'Edit Activity' : 'Add New Activity'}</DialogTitle>
                        <DialogDescription>Enter activity details manually below.</DialogDescription>
                    </DialogHeader>
                    <div className="grid grid-cols-2 gap-4 py-4">
                        <div className="space-y-2">
                            <label className="text-xs font-semibold">Activity ID</label>
                            <Input value={editingActivity?.activity_id || ''} onChange={e => setEditingActivity({ ...editingActivity, activity_id: e.target.value })} />
                        </div>
                        <div className="space-y-2">
                            <label className="text-xs font-semibold">ERC Code</label>
                            <Input value={editingActivity?.erc_code || ''} onChange={e => setEditingActivity({ ...editingActivity, erc_code: e.target.value })} />
                        </div>
                        <div className="space-y-2 col-span-2">
                            <label className="text-xs font-semibold">Activity Name</label>
                            <Input value={editingActivity?.activity_name || ''} onChange={e => setEditingActivity({ ...editingActivity, activity_name: e.target.value })} />
                        </div>
                        <div className="space-y-2">
                            <label className="text-xs font-semibold">Duration</label>
                            <Input type="number" value={editingActivity?.original_duration || ''} onChange={e => setEditingActivity({ ...editingActivity, original_duration: parseFloat(e.target.value) })} />
                        </div>
                        <div className="space-y-2">
                            <label className="text-xs font-semibold">Budgeted Cost</label>
                            <Input type="number" value={editingActivity?.budgeted_total_cost || ''} onChange={e => setEditingActivity({ ...editingActivity, budgeted_total_cost: e.target.value })} />
                        </div>
                        <div className="space-y-2">
                            <label className="text-xs font-semibold">Source Sheet</label>
                            <select
                                className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
                                value={editingActivity?.primavera_sheet || ''}
                                onChange={e => setEditingActivity({ ...editingActivity, primavera_sheet: parseInt(e.target.value) })}
                            >
                                <option value="">Select Sheet</option>
                                {sheets.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                            </select>
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setIsActivityModalOpen(false)}>Cancel</Button>
                        <Button onClick={handleSaveActivity}>Save Activity</Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
