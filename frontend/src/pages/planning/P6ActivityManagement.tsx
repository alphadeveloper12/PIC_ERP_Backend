import { useState, useEffect } from 'react';
import api from '@/services/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
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
    Edit,
    Filter,
    ArrowUpDown
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

export default function P6ActivityManagement() {
    const [activities, setActivities] = useState<P6Activity[]>([]);
    const [totalActivities, setTotalActivities] = useState(0);
    const [page, setPage] = useState(1);
    const [search, setSearch] = useState('');
    const [loading, setLoading] = useState(false);
    const [sheets, setSheets] = useState<any[]>([]);
    const [selectedSheet, setSelectedSheet] = useState<string>('');

    // Edit/Add state
    const [editingActivity, setEditingActivity] = useState<Partial<P6Activity> | null>(null);
    const [isDialogOpen, setIsDialogOpen] = useState(false);

    const fetchSheets = async () => {
        try {
            const res = await api.get('/planning/primavera-sheets/');
            setSheets(res.data);
        } catch (e) {
            console.error(e);
        }
    };

    const fetchActivities = async () => {
        setLoading(true);
        try {
            let url = `/planning/p6-activities/?page=${page}&search=${search}`;
            if (selectedSheet) url += `&primavera_sheet=${selectedSheet}`;
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

    useEffect(() => {
        fetchSheets();
    }, []);

    useEffect(() => {
        fetchActivities();
    }, [page, search, selectedSheet]);

    const handleSave = async () => {
        try {
            if (editingActivity?.id) {
                await api.put(`/planning/p6-activities/${editingActivity.id}/`, editingActivity);
                toast.success("Activity updated successfully");
            } else {
                await api.post('/planning/p6-activities/', editingActivity);
                toast.success("Activity created successfully");
            }
            setIsDialogOpen(false);
            fetchActivities();
        } catch (e) {
            console.error(e);
            toast.error("Failed to save activity");
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-foreground">P6 Activities Registry</h1>
                    <p className="text-muted-foreground mt-1 text-sm">
                        Total {totalActivities} activities found in system.
                    </p>
                </div>
                <div className="flex gap-3">
                    <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                        <DialogTrigger asChild>
                            <Button onClick={() => setEditingActivity({})}>
                                <Plus className="mr-2 h-4 w-4" /> Add Activity
                            </Button>
                        </DialogTrigger>
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
                                <Button variant="outline" onClick={() => setIsDialogOpen(false)}>Cancel</Button>
                                <Button onClick={handleSave}>Save Activity</Button>
                            </DialogFooter>
                        </DialogContent>
                    </Dialog>
                </div>
            </div>

            <Card className="border-primary/10 shadow-sm overflow-hidden">
                <CardHeader className="bg-muted/30 pb-4">
                    <div className="flex flex-col md:flex-row md:items-center gap-4">
                        <div className="relative flex-1">
                            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                            <Input
                                placeholder="Search by ID or Name..."
                                className="pl-9 h-10"
                                value={search}
                                onChange={e => { setSearch(e.target.value); setPage(1); }}
                            />
                        </div>
                        <div className="flex items-center gap-2">
                            <Filter className="h-4 w-4 text-muted-foreground" />
                            <select
                                className="h-10 rounded-md border border-input bg-background px-3 py-2 text-sm min-w-[200px]"
                                value={selectedSheet}
                                onChange={e => { setSelectedSheet(e.target.value); setPage(1); }}
                            >
                                <option value="">All Uploaded Sheets</option>
                                {sheets.map(s => <option key={s.id} value={s.id}>{s.name} ({s.uploaded_at.split('T')[0]})</option>)}
                            </select>
                        </div>
                    </div>
                </CardHeader>
                <CardContent className="p-0">
                    <div className="overflow-x-auto">
                        <Table>
                            <TableHeader>
                                <TableRow className="bg-muted/50 text-[10px] uppercase tracking-wider">
                                    <TableHead className="w-[120px] font-bold">Activity ID</TableHead>
                                    <TableHead className="font-bold">Activity Name</TableHead>
                                    <TableHead className="w-[120px] font-bold text-blue-600">Early S/F</TableHead>
                                    <TableHead className="w-[120px] font-bold text-orange-600">Late S/F</TableHead>
                                    <TableHead className="w-[120px] font-bold text-green-600">Actual S/F</TableHead>
                                    <TableHead className="w-[100px] font-bold text-right">Cost</TableHead>
                                    <TableHead className="w-[60px]"></TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {loading ? (
                                    <TableRow>
                                        <TableCell colSpan={7} className="text-center py-20">
                                            <Loading message="Fetching activities..." />
                                        </TableCell>
                                    </TableRow>
                                ) : activities.length === 0 ? (
                                    <TableRow>
                                        <TableCell colSpan={7} className="text-center py-20 text-muted-foreground">
                                            No activities found matching criteria.
                                        </TableCell>
                                    </TableRow>
                                ) : activities.map((act) => (
                                    <TableRow key={act.id} className="hover:bg-muted/20 transition-colors border-b">
                                        <TableCell className="font-mono text-[10px] font-bold text-primary">{act.activity_id}</TableCell>
                                        <TableCell className="text-xs font-medium max-w-[200px]">
                                            <div className="truncate" title={act.activity_name}>{act.activity_name}</div>
                                            <div className="text-[9px] text-muted-foreground mt-0.5">{act.erc_code || 'No ERC'}</div>
                                        </TableCell>
                                        <TableCell className="text-[10px] text-blue-700 font-medium">
                                            <div className="flex flex-col">
                                                <span>S: {act.early_start ? act.early_start.split('T')[0] : '---'}</span>
                                                <span>F: {act.early_finish ? act.early_finish.split('T')[0] : '---'}</span>
                                            </div>
                                        </TableCell>
                                        <TableCell className="text-[10px] text-orange-700 font-medium">
                                            <div className="flex flex-col">
                                                <span>S: {act.late_start ? act.late_start.split('T')[0] : '---'}</span>
                                                <span>F: {act.late_finish ? act.late_finish.split('T')[0] : '---'}</span>
                                            </div>
                                        </TableCell>
                                        <TableCell className="text-[10px] text-green-700 font-bold">
                                            <div className="flex flex-col">
                                                <span>S: {act.actual_start ? act.actual_start.split('T')[0] : '---'}</span>
                                                <span>F: {act.actual_finish ? act.actual_finish.split('T')[0] : '---'}</span>
                                            </div>
                                        </TableCell>
                                        <TableCell className="text-right text-xs tabular-nums font-bold">
                                            {act.budgeted_total_cost ? parseFloat(act.budgeted_total_cost).toLocaleString() : '0'}
                                        </TableCell>
                                        <TableCell>
                                            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => { setEditingActivity(act); setIsDialogOpen(true); }}>
                                                <Edit className="h-3 w-3" />
                                            </Button>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </div>

                    {/* Pagination */}
                    <div className="flex items-center justify-between p-4 border-t bg-muted/5">
                        <div className="text-sm text-muted-foreground">
                            Showing <span className="font-medium">{(page - 1) * 5 + 1}</span> to <span className="font-medium">{Math.min(page * 5, totalActivities)}</span> of <span className="font-medium">{totalActivities}</span> activities
                        </div>
                        <div className="flex gap-2">
                            <Button
                                variant="outline"
                                size="sm"
                                disabled={page === 1}
                                onClick={() => setPage(p => p - 1)}
                            >
                                <ChevronLeft className="h-4 w-4 mr-1" /> Previous
                            </Button>
                            <Button
                                variant="outline"
                                size="sm"
                                disabled={page * 5 >= totalActivities}
                                onClick={() => setPage(p => p + 1)}
                            >
                                Next <ChevronRight className="h-4 w-4 ml-1" />
                            </Button>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
