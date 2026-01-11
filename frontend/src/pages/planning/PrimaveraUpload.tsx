import { useEffect, useState } from 'react';
import api from '@/services/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Upload, FileUp, CheckCircle, Plus } from 'lucide-react';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import { toast } from 'sonner';
import { Loading } from '@/components/Loading';

interface Project {
    id: number;
    name: string;
}

interface SubPhase {
    id: number;
    name: string;
}

export default function PrimaveraUpload() {
    const [projects, setProjects] = useState<Project[]>([]);
    const [subPhases, setSubPhases] = useState<SubPhase[]>([]);

    const [selectedProject, setSelectedProject] = useState('');
    const [selectedSubPhase, setSelectedSubPhase] = useState('');
    const [file, setFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);
    const [result, setResult] = useState<any>(null);

    // New Subphase State
    const [isSubphaseModalOpen, setIsSubphaseModalOpen] = useState(false);
    const [newSubphaseName, setNewSubphaseName] = useState('');
    const [isCreatingSubphase, setIsCreatingSubphase] = useState(false);

    useEffect(() => {
        // Fetch Projects scoped to user ownership
        api.get('/api/project/list?mode=my_projects').then(res => setProjects(res.data.data)).catch(console.error);
    }, []);

    const fetchSubphases = async (projectId: string) => {
        try {
            const res = await api.get(`/api/subphase/list?project_id=${projectId}`);
            setSubPhases(res.data.data);
        } catch (e) {
            console.error(e);
        }
    };

    useEffect(() => {
        if (selectedProject) {
            fetchSubphases(selectedProject);
        } else {
            setSubPhases([]);
        }
    }, [selectedProject]);

    const handleCreateSubphase = async () => {
        if (!newSubphaseName || !selectedProject) return;
        setIsCreatingSubphase(true);
        try {
            await api.post('/api/subphase/create', {
                name: newSubphaseName,
                project: selectedProject
            });
            toast.success("Subphase created successfully");
            setNewSubphaseName('');
            setIsSubphaseModalOpen(false);
            fetchSubphases(selectedProject);
        } catch (e) {
            console.error(e);
            toast.error("Failed to create subphase");
        } finally {
            setIsCreatingSubphase(false);
        }
    };

    const handleUpload = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!file || !selectedSubPhase) return;

        setUploading(true);
        const formData = new FormData();
        formData.append('file', file);
        formData.append('subphase_id', selectedSubPhase);
        formData.append('name', file.name);

        try {
            const res = await api.post('/planning/primavera-sheets/import_data/', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            setResult(res.data);
            toast.success('Import Successful!');
        } catch (err: any) {
            console.error(err);
            toast.error('Upload failed: ' + (err.response?.data?.error || 'Unknown error'));
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="space-y-6 max-w-5xl mx-auto p-4 md:p-8">
            {uploading && <Loading fullPage message="Processing Primavera Data & Generating Tasks..." />}
            <h1 className="text-4xl font-extrabold tracking-tight text-foreground">Primavera Upload</h1>
            <p className="text-muted-foreground -mt-4">Import your P6 activity data to generate DMS tasks automatically.</p>

            <div className="grid gap-8 md:grid-cols-3">
                <Card className="md:col-span-2 shadow-xl border-primary/5">
                    <CardHeader className="border-b bg-muted/30">
                        <CardTitle className="text-xl">Upload Configuration</CardTitle>
                        <CardDescription>
                            Define the project target and upload your P6 Export (.xls/.xlsx).
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="pt-6">
                        <form onSubmit={handleUpload} className="space-y-6">
                            <div className="grid gap-3">
                                <Label htmlFor="project" className="text-sm font-bold">Project</Label>
                                <select
                                    id="project"
                                    className="flex h-11 w-full rounded-lg border border-input bg-background px-4 py-2 text-sm shadow-sm transition-colors focus:ring-2 focus:ring-primary/20 outline-none"
                                    value={selectedProject}
                                    onChange={e => setSelectedProject(e.target.value)}
                                    required
                                >
                                    <option value="">Select Project</option>
                                    {projects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                                </select>
                            </div>

                            <div className="grid gap-3">
                                <div className="flex justify-between items-center">
                                    <Label htmlFor="subphase" className="text-sm font-bold">Sub-Phase</Label>
                                    {selectedProject && (
                                        <Dialog open={isSubphaseModalOpen} onOpenChange={setIsSubphaseModalOpen}>
                                            <DialogTrigger asChild>
                                                <Button type="button" variant="link" size="sm" className="h-auto p-0 text-primary font-bold flex items-center gap-1">
                                                    <Plus className="h-3 w-3" /> Add New Sub-Phase
                                                </Button>
                                            </DialogTrigger>
                                            <DialogContent>
                                                <DialogHeader>
                                                    <DialogTitle>Create New Sub-Phase</DialogTitle>
                                                    <DialogDescription>
                                                        Add a new phase for project: {projects.find(p => p.id.toString() === selectedProject)?.name}
                                                    </DialogDescription>
                                                </DialogHeader>
                                                <div className="py-4">
                                                    <Label htmlFor="newSubphase" className="text-sm font-medium mb-2 block text-foreground">Phase Name</Label>
                                                    <Input
                                                        id="newSubphase"
                                                        placeholder="e.g. Tendering Phase"
                                                        value={newSubphaseName}
                                                        onChange={e => setNewSubphaseName(e.target.value)}
                                                    />
                                                </div>
                                                <DialogFooter>
                                                    <Button variant="outline" onClick={() => setIsSubphaseModalOpen(false)}>Cancel</Button>
                                                    <Button onClick={handleCreateSubphase} disabled={isCreatingSubphase || !newSubphaseName}>
                                                        {isCreatingSubphase ? 'Creating...' : 'Create Phase'}
                                                    </Button>
                                                </DialogFooter>
                                            </DialogContent>
                                        </Dialog>
                                    )}
                                </div>
                                <select
                                    id="subphase"
                                    className="flex h-11 w-full rounded-lg border border-input bg-background px-4 py-2 text-sm shadow-sm transition-colors focus:ring-2 focus:ring-primary/20 outline-none disabled:bg-muted/50"
                                    value={selectedSubPhase}
                                    onChange={e => setSelectedSubPhase(e.target.value)}
                                    required
                                    disabled={!selectedProject}
                                >
                                    <option value="">Select Sub-Phase</option>
                                    {subPhases.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                                </select>
                                {selectedProject && subPhases.length === 0 && (
                                    <p className="text-xs text-orange-600 font-medium">No sub-phases found for this project. Please add one above.</p>
                                )}
                            </div>

                            <div className="grid gap-3">
                                <Label htmlFor="file" className="text-sm font-bold">P6 Excel File</Label>
                                <div className="relative group">
                                    <Input
                                        id="file"
                                        type="file"
                                        accept=".xls,.xlsx"
                                        className="h-20 pt-8 pb-2 px-10 cursor-pointer text-center bg-muted/5 border-dashed border-2 group-hover:bg-primary/5 group-hover:border-primary transition-all"
                                        onChange={e => setFile(e.target.files ? e.target.files[0] : null)}
                                        required
                                    />
                                    <FileUp className="absolute top-3 left-1/2 -ml-3 h-6 w-6 text-muted-foreground group-hover:text-primary transition-colors" />
                                    {file && (
                                        <div className="absolute top-10 w-full text-center">
                                            <span className="text-xs font-medium text-primary bg-primary/10 px-2 py-0.5 rounded-full">{file.name}</span>
                                        </div>
                                    )}
                                </div>
                            </div>

                            <Button type="submit" className="w-full h-12 text-base font-bold shadow-lg" disabled={uploading || !selectedSubPhase || !file}>
                                {uploading ? <Upload className="mr-3 h-5 w-5 animate-spin" /> : <FileUp className="mr-3 h-5 w-5" />}
                                {uploading ? 'Importing & Generating Tasks...' : 'Upload & Process Data'}
                            </Button>
                        </form>
                    </CardContent>
                </Card>

                <div className="space-y-6">
                    {result && (
                        <Card className="bg-green-50/50 border-green-200 shadow-lg animate-in fade-in zoom-in-95 duration-300">
                            <CardHeader className="pb-2">
                                <CardTitle className="flex items-center gap-2 text-green-700 text-lg">
                                    <CheckCircle className="h-5 w-5" /> Import Complete
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="text-sm space-y-3">
                                <div className="p-3 bg-white rounded-lg border border-green-100 shadow-sm">
                                    <p className="flex justify-between font-medium"><span>Sheet ID:</span> <span className="text-primary">#{result.sheet_id}</span></p>
                                    <p className="flex justify-between font-medium mt-1"><span>Tasks Created:</span> <span className="text-primary">{result.tasks_generated}</span></p>
                                </div>
                                {result.import_stats && (
                                    <div className="bg-white p-3 rounded-lg border border-green-100 shadow-sm overflow-hidden">
                                        <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-2">Detailed Stats</p>
                                        <pre className="text-[11px] leading-relaxed overflow-auto max-h-40">{JSON.stringify(result.import_stats, null, 2)}</pre>
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    )}

                    <Card className="bg-primary/5 border-none">
                        <CardHeader>
                            <CardTitle className="text-sm">Requirements</CardTitle>
                        </CardHeader>
                        <CardContent className="text-xs text-muted-foreground space-y-2 leading-relaxed">
                            <p>• File must be in <strong>.xls</strong> or <strong>.xlsx</strong> format.</p>
                            <p>• Ensure columns for <strong>Activity ID</strong>, <strong>Activity Name</strong>, and <strong>Dates</strong> are present.</p>
                            <p>• Tasks will be assigned to departments based on automatic matching logic.</p>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
