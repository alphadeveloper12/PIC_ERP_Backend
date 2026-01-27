import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '@/services/api';
import { useAuthStore } from '@/hooks/useAuthStore';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import {
    FileText,
    Calendar,
    User,
    ArrowLeft,
    CheckCircle,
    MessageSquare,
    History,
    FileUp,
    Download,
    ExternalLink,
    AlertCircle,
    Info
} from 'lucide-react';
import { Loading } from '@/components/Loading';
import { toast } from "sonner";
import { cn } from "@/lib/utils";

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
        required_document_type?: string;
    };
    project_name: string;
    p6_activity_name?: string;
    project: number;
    status: string;
    comments: string;
    assigned_to_details?: {
        id: number;
        username: string;
        first_name: string;
        last_name: string;
    };
    created_at: string;
    completed_at?: string;
    documents: Document[];
    related_documents?: Document[];
    due_date?: string;
    early_start?: string;
    early_finish?: string;
}

export default function TaskDetail() {
    const { id } = useParams();
    const navigate = useNavigate();
    const { user } = useAuthStore();
    const [task, setTask] = useState<Task | null>(null);
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState(false);

    // Upload state
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [docType, setDocType] = useState('');
    const [actionComment, setActionComment] = useState('');

    const fetchTask = async () => {
        try {
            const res = await api.get(`/dms/tasks/${id}/`);
            setTask(res.data);
        } catch (e: any) {
            console.error(e);
            toast.error("Failed to load task details");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTask();
    }, [id]);

    const handleUpload = async () => {
        if (!selectedFile || !docType) return;
        setActionLoading(true);
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('document_type', docType);
        formData.append('task', id!);
        formData.append('project', task?.project.toString() || '');

        try {
            await api.post('/dms/documents/', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            toast.success("Document uploaded successfully");
            setSelectedFile(null);
            setDocType('');
            fetchTask();
        } catch (e) {
            console.error(e);
            toast.error("Upload failed");
        } finally {
            setActionLoading(false);
        }
    };

    const handleAction = async (action: string) => {
        setActionLoading(true);
        try {
            await api.post(`/dms/tasks/${id}/perform_action/`, {
                action,
                comments: actionComment
            });
            toast.success(`Task ${action.toLowerCase()} successfully`);
            setActionComment('');
            if (action === 'SUBMIT' || action === 'APPROVE') {
                // Refresh or navigate? Stay for now to see result
                fetchTask();
            } else {
                fetchTask();
            }
        } catch (e: any) {
            console.error(e);
            toast.error(e.response?.data?.error || `Failed to ${action.toLowerCase()} task`);
        } finally {
            setActionLoading(false);
        }
    };

    if (loading) return <Loading fullPage message="Entering Task Workspace..." />;
    if (!task) return <div className="p-10 text-center">Task not found</div>;

    const isAssignedToMe = task.assigned_to_details?.id === user?.id;
    const canSubmit = isAssignedToMe && ['ASSIGNED', 'IN_PROGRESS', 'PENDING'].includes(task.status);
    const canApprove = (user?.is_owner || user?.is_hod) && task.status === 'SUBMITTED';

    return (
        <div className="max-w-7xl mx-auto space-y-8 pb-20 px-4 mt-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Breadcrumbs & Header */}
            <div className="flex flex-col gap-4">
                <Button
                    variant="ghost"
                    size="sm"
                    className="w-fit gap-2 -ml-2 text-muted-foreground hover:text-foreground"
                    onClick={() => navigate('/dms')}
                >
                    <ArrowLeft className="h-4 w-4" /> Back to Dashboard
                </Button>

                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                    <div className="space-y-2">
                        <div className="flex items-center gap-3">
                            <span className="bg-primary/10 text-primary text-[10px] font-black uppercase tracking-widest px-2 py-1 rounded border border-primary/20">
                                {task.workflow_step_details?.sequence_id || 'Custom Task'}
                            </span>
                            <span className={cn(
                                "text-[10px] font-black uppercase tracking-widest px-2 py-1 rounded border",
                                task.status === 'APPROVED' ? "bg-green-100 text-green-700 border-green-200" :
                                    task.status === 'SUBMITTED' ? "bg-blue-100 text-blue-700 border-blue-200" :
                                        "bg-orange-100 text-orange-700 border-orange-200"
                            )}>
                                {task.status.replace('_', ' ')}
                            </span>
                        </div>
                        <h1 className="text-2xl font-black tracking-tight text-foreground leading-tight max-w-2xl">
                            {task.p6_activity_name || task.workflow_step_details?.action_description}
                        </h1>
                        <p className="text-muted-foreground font-medium flex items-center gap-2">
                            <AlertCircle className="h-4 w-4 text-primary" />
                            Project: <span className="font-bold text-foreground">{task.project_name}</span>
                        </p>
                    </div>

                    <div className="flex flex-wrap gap-3">
                        {canSubmit && (
                            <div className="flex gap-2">
                                {task.status !== 'IN_PROGRESS' && (
                                    <Button
                                        variant="outline"
                                        className="h-11 px-6 border-primary/20"
                                        onClick={() => handleAction('START')}
                                        disabled={actionLoading}
                                    >
                                        Start Work
                                    </Button>
                                )}
                                <Button
                                    className="h-11 px-8 shadow-lg shadow-primary/20"
                                    onClick={() => handleAction('SUBMIT')}
                                    disabled={actionLoading}
                                >
                                    Complete & Send for Review
                                </Button>
                            </div>
                        )}
                        {/* HOD Buttons are now in the Reviewer Actions card below for better UX */}
                    </div>
                </div>
            </div>

            {/* Reviewer Actions (Prominent for HODs) */}
            {canApprove && (
                <Card className="border-primary bg-primary/5 shadow-xl animate-in zoom-in-95 duration-300">
                    <CardHeader className="pb-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <CardTitle className="text-xl font-bold flex items-center gap-2">
                                    <CheckCircle className="h-5 w-5 text-primary" /> Reviewer Decision Center
                                </CardTitle>
                                <CardDescription>You are reviewing this task. Provide feedback before taking an action.</CardDescription>
                            </div>
                        </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="space-y-2">
                            <Label className="text-xs font-black uppercase text-primary/70 tracking-widest">
                                Reviewer Remarks <span className="text-red-500">* Required for Rejection</span>
                            </Label>
                            <Textarea
                                placeholder="Write your feedback here... (e.g., 'Work looks good' or 'Please update the material list')"
                                value={actionComment}
                                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setActionComment(e.target.value)}
                                className="h-28 resize-none border-primary/20 bg-white ring-offset-primary focus-visible:ring-primary"
                                autoFocus
                            />
                        </div>
                        <div className="flex justify-end gap-3">
                            <Button
                                variant="outline"
                                className="h-12 px-8 border-red-200 text-red-700 hover:bg-red-100 hover:text-red-800 transition-all font-bold"
                                onClick={() => {
                                    if (!actionComment.trim()) {
                                        toast.error("Feedback is required to reject a task.");
                                        return;
                                    }
                                    handleAction('REJECT');
                                }}
                                disabled={actionLoading}
                            >
                                Send Back for Revision (Reject)
                            </Button>
                            <Button
                                className="h-12 px-10 shadow-lg shadow-green-200 bg-green-600 hover:bg-green-700 text-white border-none font-bold"
                                onClick={() => handleAction('APPROVE')}
                                disabled={actionLoading}
                            >
                                Approve Submission
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left Column: Details & Upload */}
                <div className="lg:col-span-2 space-y-8">
                    {/* Activity Context Card */}
                    <Card className="border-primary/10 shadow-sm">
                        <CardHeader className="bg-muted/30 border-b py-3">
                            <CardTitle className="text-xs font-black uppercase tracking-widest flex items-center gap-2">
                                <Calendar className="h-4 w-4 text-primary" /> Schedule Meta
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="grid grid-cols-2 md:grid-cols-4 gap-6 p-6">
                            <div className="space-y-1">
                                <p className="text-[10px] font-bold text-muted-foreground uppercase">Start Date</p>
                                <p className="font-mono text-sm font-black text-foreground">
                                    {task.early_start ? new Date(task.early_start).toLocaleDateString() : '---'}
                                </p>
                            </div>
                            <div className="space-y-1">
                                <p className="text-[10px] font-bold text-muted-foreground uppercase">Estimated End</p>
                                <p className="font-mono text-sm font-black text-primary">
                                    {task.early_finish ? new Date(task.early_finish).toLocaleDateString() : '---'}
                                </p>
                            </div>
                            <div className="space-y-1">
                                <p className="text-[10px] font-bold text-muted-foreground uppercase">Assigned To</p>
                                <div className="flex items-center gap-2">
                                    <div className="h-6 w-6 rounded-full bg-primary/10 flex items-center justify-center">
                                        <User className="h-3 w-3 text-primary" />
                                    </div>
                                    <p className="text-sm font-bold truncate">
                                        {task.assigned_to_details ? `${task.assigned_to_details.first_name} ${task.assigned_to_details.last_name}` : 'Unassigned'}
                                    </p>
                                </div>
                            </div>
                            <div className="space-y-1">
                                <p className="text-[10px] font-bold text-muted-foreground uppercase">Due Date</p>
                                <p className={cn(
                                    "text-sm font-black",
                                    task.due_date && new Date(task.due_date) < new Date() ? "text-red-600" : "text-foreground"
                                )}>
                                    {task.due_date ? new Date(task.due_date).toLocaleDateString() : 'Flexible'}
                                </p>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Submission Workspace */}
                    {task.status !== 'APPROVED' && (
                        <Card className="border-primary/10 shadow-lg">
                            <CardHeader className="pb-4">
                                <CardTitle className="text-xl font-bold">Document Submission</CardTitle>
                                <CardDescription>Upload supporting evidence, certificates, or lists for this task.</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-6">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div className="space-y-2">
                                        <Label className="text-xs font-bold uppercase text-muted-foreground">Document Label</Label>
                                        <Input
                                            placeholder="e.g. Material Approval Certificate"
                                            value={docType}
                                            onChange={e => setDocType(e.target.value)}
                                            className="border-primary/20 h-11"
                                        />
                                        {task.workflow_step_details?.required_document_type && (
                                            <p className="text-[10px] text-primary font-black uppercase flex items-center gap-1">
                                                <Info className="h-3 w-3" /> Required: {task.workflow_step_details.required_document_type}
                                            </p>
                                        )}
                                    </div>

                                    <div className="space-y-2">
                                        <Label className="text-xs font-bold uppercase text-muted-foreground">Select File</Label>
                                        <div className="flex gap-2">
                                            <div className="relative flex-1">
                                                <Input
                                                    type="file"
                                                    className="opacity-0 absolute inset-0 w-full h-full cursor-pointer z-10"
                                                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSelectedFile(e.target.files?.[0] || null)}
                                                />
                                                <div className="h-11 border border-primary/20 rounded-md flex items-center px-4 text-sm text-muted-foreground bg-muted/5 truncate">
                                                    {selectedFile ? selectedFile.name : "Choose file..."}
                                                </div>
                                            </div>
                                            <Button
                                                onClick={handleUpload}
                                                disabled={!selectedFile || !docType || actionLoading}
                                                className="h-11 px-6 gap-2"
                                            >
                                                <FileUp className="h-4 w-4" /> Upload
                                            </Button>
                                        </div>
                                    </div>
                                </div>

                                {isAssignedToMe && (
                                    <div className="space-y-2 px-1">
                                        <Label className="text-xs font-bold uppercase text-muted-foreground">Action Remarks / Submission Notes</Label>
                                        <Textarea
                                            placeholder="Discuss progress or mention specific details about the upload..."
                                            value={actionComment}
                                            onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setActionComment(e.target.value)}
                                            className="h-24 resize-none border-primary/20"
                                        />
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    )}

                    {/* Timeline of Events */}
                    <div className="space-y-6">
                        <div className="flex items-center justify-between px-2">
                            <h3 className="text-xl font-black flex items-center gap-2">
                                <History className="h-5 w-5 text-primary" /> Submission History
                            </h3>
                            <span className="text-[10px] font-black bg-muted px-2 py-1 rounded text-muted-foreground uppercase">
                                {task.documents.length} Artifacts
                            </span>
                        </div>

                        {task.documents.length === 0 ? (
                            <div className="py-20 border-2 border-dashed rounded-3xl text-center bg-muted/5 border-primary/10">
                                <FileUp className="h-12 w-12 text-muted-foreground/20 mx-auto mb-4" />
                                <p className="text-muted-foreground font-bold">No documents have been recorded yet.</p>
                                <p className="text-xs text-muted-foreground/60 mt-1">Uploaded files will appear in a chronological timeline here.</p>
                            </div>
                        ) : (
                            <div className="relative space-y-10 pl-4 before:absolute before:inset-0 before:left-9 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-primary/60 before:via-primary/20 before:to-transparent">
                                {task.documents.map((doc) => (
                                    <div key={doc.id} className="relative flex items-start gap-8 group">
                                        <div className="absolute left-0 mt-2 h-10 w-10 rounded-xl bg-white border-2 border-primary/20 shadow-sm flex items-center justify-center text-primary z-10 transition-all group-hover:bg-primary group-hover:text-white group-hover:border-primary">
                                            <FileText className="h-5 w-5" />
                                        </div>
                                        <Card className="flex-1 border-primary/10 hover:border-primary/40 transition-all shadow-sm group-hover:shadow-md">
                                            <CardContent className="p-4 flex flex-col sm:flex-row justify-between sm:items-center gap-4">
                                                <div className="space-y-1">
                                                    <div className="flex items-center gap-2">
                                                        <span className="text-sm font-black text-foreground">{doc.document_type}</span>
                                                        <span className="text-[10px] text-muted-foreground font-bold">• {new Date(doc.created_at).toLocaleString()}</span>
                                                    </div>
                                                    <p className="text-[10px] font-black uppercase text-primary/80">
                                                        Action by {doc.uploaded_by.first_name} {doc.uploaded_by.last_name}
                                                    </p>
                                                </div>
                                                <a
                                                    href={doc.file}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="h-10 px-4 gap-2 border border-primary/20 rounded-lg flex items-center justify-center hover:bg-primary hover:text-white transition-all text-xs font-bold"
                                                >
                                                    <Download className="h-4 w-4" /> View Document
                                                </a>
                                            </CardContent>
                                        </Card>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* Right Column: Workflow & Context */}
                <div className="space-y-8">
                    {/* Status Tracker */}
                    <Card className="border-primary/10 shadow-sm bg-primary/5">
                        <CardHeader className="pb-3 px-6 pt-6">
                            <CardTitle className="text-xs font-black uppercase tracking-widest flex items-center gap-2">
                                <CheckCircle className="h-4 w-4 text-green-600" /> Progression Status
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="px-6 pb-6 space-y-4">
                            <div className="p-4 bg-white rounded-xl border border-primary/5 shadow-sm space-y-3">
                                <div className="flex items-center justify-between">
                                    <span className="text-[10px] font-bold text-muted-foreground uppercase">Current Phase</span>
                                    <span className="text-[10px] font-black text-primary uppercase">{task.status.replace('_', ' ')}</span>
                                </div>
                                <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-primary transition-all duration-1000"
                                        style={{ width: task.status === 'APPROVED' ? '100%' : task.status === 'SUBMITTED' ? '75%' : task.status === 'IN_PROGRESS' ? '40%' : '15%' }}
                                    />
                                </div>
                                <p className="text-[11px] text-muted-foreground leading-relaxed font-medium">
                                    {task.status === 'APPROVED' ? "Task is closed. Schedule sync complete." :
                                        task.status === 'REJECTED' ? "Revision required. Please address reviewer comments and resubmit." :
                                            task.status === 'SUBMITTED' ? "Under HOD review. Sync will occur upon approval." :
                                                "In transition. Complete artifacts and mark as complete to move to next stage."}
                                </p>
                            </div>

                            {task.comments && (
                                <div className={cn(
                                    "p-4 rounded-xl space-y-2 border shadow-sm animate-pulse-slow",
                                    task.status === 'REJECTED' ? "bg-red-50 border-red-200" : "bg-primary/10 border-primary/5"
                                )}>
                                    <span className={cn(
                                        "text-[10px] font-black uppercase flex items-center gap-1",
                                        task.status === 'REJECTED' ? "text-red-700" : "text-primary"
                                    )}>
                                        <MessageSquare className="h-3 w-3" />
                                        {task.status === 'REJECTED' ? "Reviewer Remarks (Revision Needed)" : "Note from System/Reviewer"}
                                    </span>
                                    <p className={cn(
                                        "text-xs font-medium italic",
                                        task.status === 'REJECTED' ? "text-red-900" : "text-foreground"
                                    )}>"{task.comments}"</p>
                                </div>
                            )}
                        </CardContent>
                    </Card>

                    {/* Historical Traceability */}
                    {task.related_documents && task.related_documents.length > 0 && (
                        <div className="space-y-4 pt-4 border-t border-muted">
                            <h4 className="text-[10px] font-black uppercase tracking-widest text-muted-foreground px-2">Inherited Context</h4>
                            <div className="space-y-3">
                                {task.related_documents.map((doc, idx) => (
                                    <div key={idx} className="flex items-center gap-4 p-3 bg-white hover:bg-muted/50 rounded-xl border border-primary/5 shadow-sm transition-all group">
                                        <div className="h-9 w-9 rounded-lg bg-muted flex items-center justify-center text-muted-foreground group-hover:text-primary group-hover:bg-primary/10 transition-all">
                                            <FileText className="h-4 w-4" />
                                        </div>
                                        <div className="flex-1 overflow-hidden">
                                            <p className="text-[11px] font-black truncate">{doc.document_type}</p>
                                            <p className="text-[10px] text-muted-foreground font-medium">{new Date(doc.created_at).toLocaleDateString()}</p>
                                        </div>
                                        <a href={doc.file} target="_blank" rel="noreferrer" className="p-2 opacity-40 hover:opacity-100">
                                            <ExternalLink className="h-3.5 w-3.5" />
                                        </a>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
