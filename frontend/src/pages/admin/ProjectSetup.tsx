import { useEffect, useState } from 'react';
import api from '@/services/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { UserPlus, Plus, Building } from 'lucide-react';
import { useAuthStore } from '@/hooks/useAuthStore';

interface Project {
    id: number;
    name: string;
    code: string;
    status: string;
    company: number;
    start_date: string;
    end_date: string;
}

export default function ProjectSetup() {
    const { register } = useAuthStore();
    const [projects, setProjects] = useState<Project[]>([]);
    const [loading, setLoading] = useState(false);
    const [showForm, setShowForm] = useState(false);

    // Quick Register State
    const [showRegister, setShowRegister] = useState(false);
    const [newUser, setNewUser] = useState({ username: '', email: '', password: '', first_name: '', last_name: '' });

    // ... (fetchProjects, fetchUsers)

    // Moved to top for clarity, though placement doesn't matter much in functional comp if valid closure
    const handleQuickRegister = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await register(newUser);
            alert('User Registered!');
            setShowRegister(false);
            setNewUser({ username: '', email: '', password: '', first_name: '', last_name: '' });
            await fetchUsers(); // Refresh list
            // Optionally auto-select could be hard without returning ID from register(), assume list refresh is enough
        } catch (e) {
            console.error("Quick Register Failed", e);
            alert('Registration Failed');
        }
    };


    // Form State
    const [formData, setFormData] = useState({
        name: '',
        code: '',
        company: 1, // Defaulting to 1 for now, ideally fetch companies
        status: 'planned',
        start_date: '',
        end_date: '',
        owner_user: ''
    });

    const fetchProjects = async () => {
        try {
            setLoading(true);
            const res = await api.get('/api/project/list');
            // The API returns { status: "success", data: [...] } based on views.py
            setProjects(res.data.data);
        } catch (err) {
            console.error("Failed to fetch projects", err);
        } finally {
            setLoading(false);
        }
    };

    // Users State
    const [users, setUsers] = useState<any[]>([]);

    const fetchUsers = async () => {
        try {
            const res = await api.get('/api/auth/users/'); // Confirmed path if 'api/auth/' is prefix
            setUsers(res.data);
        } catch (e) {
            console.error("Failed to fetch users", e);
        }
    };

    useEffect(() => {
        fetchProjects();
        fetchUsers();
    }, []);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await api.post('/api/project/create', formData);
            setShowForm(false);
            fetchProjects();
            setFormData({ ...formData, name: '', code: '', owner_user: '' });
        } catch (err) {
            console.error("Failed to create project", err);
            alert("Failed to create project.");
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-3xl font-bold tracking-tight">Projects</h1>
                <Button onClick={() => setShowForm(!showForm)}>
                    <Plus className="mr-2 h-4 w-4" /> New Project
                </Button>
            </div>

            {showForm && (
                <Card className="max-w-xl">
                    <CardHeader>
                        <CardTitle>Create Project</CardTitle>
                        <CardDescription>Enter project details below.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="name">Project Name</Label>
                                    <Input
                                        id="name"
                                        value={formData.name}
                                        onChange={e => setFormData({ ...formData, name: e.target.value })}
                                        required
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="code">Project Code</Label>
                                    <Input
                                        id="code"
                                        value={formData.code}
                                        onChange={e => setFormData({ ...formData, code: e.target.value })}
                                        required
                                        placeholder="PRJ-001"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="owner">Project Owner</Label>
                                    <div className="flex gap-2">
                                        <select
                                            id="owner"
                                            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                            value={formData.owner_user || ''}
                                            onChange={e => setFormData({ ...formData, owner_user: e.target.value })}
                                        >
                                            <option value="">Select Owner</option>
                                            {users.map(u => (
                                                <option key={u.id} value={u.id}>{u.username} ({u.email})</option>
                                            ))}
                                        </select>
                                        <Button type="button" size="icon" variant="outline" onClick={() => setShowRegister(true)} title="Register New User">
                                            <UserPlus className="h-4 w-4" />
                                        </Button>
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="start_date">Start Date</Label>
                                    <Input
                                        id="start_date"
                                        type="date"
                                        value={formData.start_date}
                                        onChange={e => setFormData({ ...formData, start_date: e.target.value })}
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="end_date">End Date</Label>
                                    <Input
                                        id="end_date"
                                        type="date"
                                        value={formData.end_date}
                                        onChange={e => setFormData({ ...formData, end_date: e.target.value })}
                                    />
                                </div>
                            </div>

                            <div className="flex justify-end gap-2">
                                <Button variant="outline" type="button" onClick={() => setShowForm(false)}>Cancel</Button>
                                <Button type="submit">Create Project</Button>
                            </div>
                        </form>
                    </CardContent>
                </Card>
            )}

            {/* Quick Register Modal/Card */}
            {showRegister && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <Card className="w-[400px]">
                        <CardHeader>
                            <CardTitle>Quick Register User</CardTitle>
                            <CardDescription>Register a new Project Owner.</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <form onSubmit={handleQuickRegister} className="space-y-4">
                                <div className="space-y-2">
                                    <Input placeholder="Username" value={newUser.username} onChange={e => setNewUser({ ...newUser, username: e.target.value })} required />
                                    <Input placeholder="Email" type="email" value={newUser.email} onChange={e => setNewUser({ ...newUser, email: e.target.value })} required />
                                    <Input placeholder="Password" type="password" value={newUser.password} onChange={e => setNewUser({ ...newUser, password: e.target.value })} required />
                                    <div className="grid grid-cols-2 gap-2">
                                        <Input placeholder="First Name" value={newUser.first_name} onChange={e => setNewUser({ ...newUser, first_name: e.target.value })} />
                                        <Input placeholder="Last Name" value={newUser.last_name} onChange={e => setNewUser({ ...newUser, last_name: e.target.value })} />
                                    </div>
                                </div>
                                <div className="flex justify-end gap-2">
                                    <Button variant="outline" type="button" onClick={() => setShowRegister(false)}>Cancel</Button>
                                    <Button type="submit">Register</Button>
                                </div>
                            </form>
                        </CardContent>
                    </Card>
                </div>
            )}

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {loading ? (
                    <p>Loading projects...</p>
                ) : projects.length === 0 ? (
                    <p className="text-muted-foreground">No projects found.</p>
                ) : (
                    projects.map(project => (
                        <Card key={project.id}>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-lg">{project.name}</CardTitle>
                                <CardDescription>{project.code}</CardDescription>
                            </CardHeader>
                            <CardContent>
                                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                    <Building className="h-4 w-4" />
                                    <span>Status: {project.status}</span>
                                </div>
                            </CardContent>
                        </Card>
                    ))
                )}
            </div>
        </div>
    );
}
