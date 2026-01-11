import { useEffect, useState } from 'react';
import api from '@/services/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { ChevronLeft, ChevronRight, Plus, Users, UserPlus } from 'lucide-react';
import { useAuthStore } from '@/hooks/useAuthStore';

interface Department {
    id: number;
    name: string;
    code: string;
}

interface UserRole {
    id: number;
    user: number;
    department: number;
    role: string;
    user_details: {
        username: string;
        first_name: string;
        last_name: string;
        email: string;
    };
    department_code: string;
}

export default function TeamManagement() {
    const { register } = useAuthStore();
    const [team, setTeam] = useState<UserRole[]>([]);
    const [totalTeam, setTotalTeam] = useState(0);
    const [page, setPage] = useState(1);
    const [departments, setDepartments] = useState<Department[]>([]);
    const [projects, setProjects] = useState<any[]>([]);
    const [selectedProject, setSelectedProject] = useState('');
    const [loading, setLoading] = useState(false);

    // UI Toggles
    const [showUserForm, setShowUserForm] = useState(false);
    const [showAssignForm, setShowAssignForm] = useState(false);

    const [users, setUsers] = useState<any[]>([]);
    const [assignment, setAssignment] = useState({ user_id: '', department_id: '', role: 'MEMBER' });

    // Forms
    const [newUser, setNewUser] = useState({ username: '', email: '', password: '', first_name: '', last_name: '' });

    const fetchUsers = async () => {
        try {
            const res = await api.get('/api/auth/users/');
            setUsers(res.data);
        } catch (e) {
            console.error(e);
        }
    };

    const fetchProjects = async () => {
        try {
            const res = await api.get('/api/project/list?mode=my_projects');
            setProjects(res.data.data);
            if (res.data.data.length > 0) {
                setSelectedProject(res.data.data[0].id.toString());
            }
        } catch (e) {
            console.error("Failed to fetch projects", e);
        }
    };

    const fetchData = async () => {
        if (!selectedProject) return;
        setLoading(true);
        try {
            const depsRes = await api.get('/dms/departments/');
            setDepartments(depsRes.data);

            const teamRes = await api.get(`/dms/team/?project_id=${selectedProject}&page=${page}`);
            setTeam(teamRes.data.results);
            setTotalTeam(teamRes.data.count);
        } catch (e) {
            console.error("Failed to fetch data", e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchProjects();
        fetchUsers();
    }, []);

    useEffect(() => {
        setPage(1); // Reset page when project changes
        fetchData();
    }, [selectedProject]);

    useEffect(() => {
        fetchData();
    }, [page]);

    const handleRegister = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await register(newUser);
            alert('User Registered!');
            setNewUser({ username: '', email: '', password: '', first_name: '', last_name: '' });
            setShowUserForm(false);
            fetchUsers();
        } catch (e) {
            console.error(e);
            alert('Registration Failed');
        }
    };

    const handleAssign = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedProject) {
            alert('Please select a project first');
            return;
        }
        if (!assignment.department_id || !assignment.user_id) {
            alert('Please select both a user and a department');
            return;
        }
        try {
            await api.post('/dms/team/', {
                user: assignment.user_id,
                department: assignment.department_id,
                role: assignment.role,
                project: selectedProject
            });
            alert('Assigned successfully!');
            setShowAssignForm(false);
            setAssignment({ user_id: '', department_id: '', role: 'MEMBER' });
            fetchData();
        } catch (e) {
            console.error(e);
            alert('Assignment Failed');
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div className="flex flex-col gap-1">
                    <h1 className="text-3xl font-bold tracking-tight">Team Management</h1>
                    {/* Project Selector */}
                    <div className="flex items-center gap-2 mt-2">
                        <span className="text-sm font-medium text-muted-foreground mr-2">Primary Project:</span>
                        <select
                            className="h-9 rounded-md border bg-background text-sm px-3 w-[250px] shadow-sm"
                            value={selectedProject}
                            onChange={e => setSelectedProject(e.target.value)}
                        >
                            <option value="">Select Project</option>
                            {projects.map(p => (
                                <option key={p.id} value={p.id}>{p.name} ({p.code})</option>
                            ))}
                        </select>
                    </div>
                </div>
                <div className="flex gap-2">
                    <Button variant="outline" onClick={() => setShowUserForm(!showUserForm)}>
                        <UserPlus className="mr-2 h-4 w-4" /> Register Person
                    </Button>
                    <Button onClick={() => setShowAssignForm(!showAssignForm)} disabled={!selectedProject}>
                        <Plus className="mr-2 h-4 w-4" /> Assign to Team
                    </Button>
                </div>
            </div>

            {/* Register User Form */}
            {showUserForm && (
                <Card className="border-primary/20 bg-primary/5">
                    <CardHeader>
                        <CardTitle className="text-lg">Register New Person</CardTitle>
                        <CardDescription>Create a global user profile.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleRegister} className="space-y-4">
                            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                                <Input placeholder="Username" value={newUser.username} onChange={e => setNewUser({ ...newUser, username: e.target.value })} required />
                                <Input placeholder="Email" type="email" value={newUser.email} onChange={e => setNewUser({ ...newUser, email: e.target.value })} required />
                                <Input placeholder="Password" type="password" value={newUser.password} onChange={e => setNewUser({ ...newUser, password: e.target.value })} required />
                                <Input placeholder="First Name" value={newUser.first_name} onChange={e => setNewUser({ ...newUser, first_name: e.target.value })} />
                                <Input placeholder="Last Name" value={newUser.last_name} onChange={e => setNewUser({ ...newUser, last_name: e.target.value })} />
                            </div>
                            <div className="flex justify-end gap-2">
                                <Button variant="ghost" onClick={() => setShowUserForm(false)}>Cancel</Button>
                                <Button type="submit">Register</Button>
                            </div>
                        </form>
                    </CardContent>
                </Card>
            )}

            {/* Assign Member Form */}
            {showAssignForm && (
                <Card className="border-primary/20">
                    <CardHeader>
                        <CardTitle className="text-lg">Assign Member to {projects.find(p => p.id == selectedProject)?.name}</CardTitle>
                        <CardDescription>Assign an existing user to a department and role.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleAssign} className="flex flex-wrap gap-4 items-end">
                            <div className="flex-1 min-w-[200px] space-y-1.5">
                                <span className="text-xs font-medium text-muted-foreground">Select User</span>
                                <select
                                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                    value={assignment.user_id}
                                    onChange={e => setAssignment({ ...assignment, user_id: e.target.value })}
                                    required
                                >
                                    <option value="">Choose User...</option>
                                    {users.map(u => (
                                        <option key={u.id} value={u.id}>{u.first_name || u.username} ({u.email})</option>
                                    ))}
                                </select>
                            </div>
                            <div className="flex-1 min-w-[200px] space-y-1.5">
                                <span className="text-xs font-medium text-muted-foreground">Department</span>
                                <select
                                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                    value={assignment.department_id}
                                    onChange={e => setAssignment({ ...assignment, department_id: e.target.value })}
                                    required
                                >
                                    <option value="">Choose Dept...</option>
                                    {departments.map(d => (
                                        <option key={d.id} value={d.id}>{d.name}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="w-[150px] space-y-1.5">
                                <span className="text-xs font-medium text-muted-foreground">Role</span>
                                <select
                                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                    value={assignment.role}
                                    onChange={e => setAssignment({ ...assignment, role: e.target.value })}
                                >
                                    <option value="MEMBER">Member</option>
                                    <option value="HOD">HOD</option>
                                    <option value="MANAGER">Manager</option>
                                    <option value="PLANNER">Planner</option>
                                </select>
                            </div>
                            <Button type="submit">Assign to Project</Button>
                        </form>
                    </CardContent>
                </Card>
            )}

            {/* Team List (Showing only assigned members) */}
            <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                    <div>
                        <CardTitle>Team Members</CardTitle>
                        <CardDescription>Manage roles for people working on this project.</CardDescription>
                    </div>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        {loading ? (
                            <p className="text-center py-8 text-muted-foreground">Loading team members...</p>
                        ) : team.length === 0 ? (
                            <div className="text-center py-12 border-2 border-dashed rounded-lg bg-muted/20">
                                <Users className="h-10 w-10 mx-auto text-muted-foreground/50 mb-4" />
                                <p className="text-muted-foreground">No team members assigned yet.</p>
                                <Button variant="link" onClick={() => setShowAssignForm(true)} className="mt-2">Assign someone now</Button>
                            </div>
                        ) : (
                            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-1">
                                {team.map(member => (
                                    <div key={member.id} className="flex items-center justify-between p-4 border rounded-lg hover:shadow-sm transition-all bg-card">
                                        <div className="flex items-center gap-4">
                                            <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center font-bold text-primary">
                                                {member.user_details.first_name?.[0]}{member.user_details.last_name?.[0]}
                                            </div>
                                            <div>
                                                <p className="font-semibold">{member.user_details.first_name} {member.user_details.last_name}</p>
                                                <p className="text-xs text-muted-foreground">@{member.user_details.username} • {member.user_details.email}</p>
                                            </div>
                                        </div>
                                        <div className="flex flex-col items-end">
                                            <div className="flex items-center gap-2">
                                                <div className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-primary/10 text-primary">
                                                    {member.role}
                                                </div>
                                            </div>
                                            <span className="text-sm font-medium mt-1">{member.department_code}</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Pagination Controls */}
                        {totalTeam > 5 && (
                            <div className="flex items-center justify-between pt-4 border-t mt-6">
                                <p className="text-sm text-muted-foreground">
                                    Showing <span className="font-medium">{(page - 1) * 5 + 1}</span> to <span className="font-medium">{Math.min(page * 5, totalTeam)}</span> of <span className="font-medium">{totalTeam}</span> results
                                </p>
                                <div className="flex gap-2">
                                    <Button
                                        variant="outline"
                                        size="icon"
                                        disabled={page === 1}
                                        onClick={() => setPage(p => p - 1)}
                                    >
                                        <ChevronLeft className="h-4 w-4" />
                                    </Button>
                                    <Button
                                        variant="outline"
                                        size="icon"
                                        disabled={page * 5 >= totalTeam}
                                        onClick={() => setPage(p => p + 1)}
                                    >
                                        <ChevronRight className="h-4 w-4" />
                                    </Button>
                                </div>
                            </div>
                        )}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
