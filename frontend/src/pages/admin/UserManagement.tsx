import { useEffect, useState } from 'react';
import api from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';

interface User {
    id: number;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    is_staff: boolean;
    is_superuser: boolean;
}

export default function UserManagement() {
    const [users, setUsers] = useState<User[]>([]);
    const [loading, setLoading] = useState(false);

    const fetchUsers = async () => {
        setLoading(true);
        try {
            const res = await api.get('/api/auth/users/');
            setUsers(res.data);
        } catch (e) {
            console.error("Failed to fetch users", e);
            // Likely 403 if not admin
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchUsers();
    }, []);

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            <header className="erp-header">
                <h1 className="text-2xl font-black tracking-tight text-foreground">User Management</h1>
                <p className="text-sm font-bold text-muted-foreground italic">System-wide user administration and role monitoring.</p>
            </header>

            <Card className="erp-card bg-card">
                <CardHeader className="pb-4">
                    <CardTitle className="text-xl font-black">Authentication Registry</CardTitle>
                    <CardDescription className="text-xs font-bold text-muted-foreground">Visible only to Superusers.</CardDescription>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>ID</TableHead>
                                <TableHead>Username</TableHead>
                                <TableHead>Email</TableHead>
                                <TableHead>Name</TableHead>
                                <TableHead>Role</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {loading ? (
                                <TableRow>
                                    <TableCell colSpan={5} className="text-center">Loading...</TableCell>
                                </TableRow>
                            ) : users.map(user => (
                                <TableRow key={user.id}>
                                    <TableCell>{user.id}</TableCell>
                                    <TableCell className="font-medium">{user.username}</TableCell>
                                    <TableCell>{user.email}</TableCell>
                                    <TableCell>{user.first_name} {user.last_name}</TableCell>
                                    <TableCell>
                                        {user.is_superuser ? <Badge variant="destructive">Superuser</Badge> :
                                            user.is_staff ? <Badge variant="default">Staff</Badge> :
                                                <Badge variant="outline">User</Badge>}
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>
        </div>
    );
}
