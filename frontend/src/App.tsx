import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import ProjectSetup from './pages/admin/ProjectSetup';
import TeamManagement from './pages/owner/TeamManagement';
import TeamPerformance from './pages/owner/TeamPerformance';
import TaskDashboard from './pages/dms/TaskDashboard';
import PermissionsManager from './pages/owner/PermissionsManager';
import UserManagement from './pages/admin/UserManagement';
import PlanningHub from './pages/planning/PlanningHub';
import TaskDetail from './pages/dms/TaskDetail';
import { NotificationsPage } from './pages/NotificationsPage';
import { useAuthStore } from './hooks/useAuthStore';
import React from 'react';

// Protected Route Wrapper (Generic)
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { token, verifySession } = useAuthStore();

  React.useEffect(() => {
    if (token) verifySession();
  }, [token]);

  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

// Admin Protected Route Wrapper (Superuser Only)
const AdminProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { token, user, verifySession } = useAuthStore();

  React.useEffect(() => {
    if (token) verifySession();
  }, [token]);

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  if (!user?.is_superuser) {
    return <Navigate to="/" replace />; // Redirect non-admins to dashboard
  }

  return children;
};

const OwnerProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { token, user, verifySession } = useAuthStore();

  React.useEffect(() => {
    if (token) verifySession();
  }, [token]);

  if (!token) return <Navigate to="/login" replace />;
  if (!user?.is_superuser && !user?.is_owner) return <Navigate to="/" replace />;
  return children;
};

const router = createBrowserRouter([
  {
    path: '/login',
    element: <Login />,
  },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <Layout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <Dashboard />,
      },
      {
        path: 'projects',
        element: (
          <AdminProtectedRoute>
            <ProjectSetup />
          </AdminProtectedRoute>
        ),
      },
      {
        path: 'team',
        element: <TeamManagement />,
      },
      {
        path: 'team/performance',
        element: <TeamPerformance />,
      },
      {
        path: 'permissions',
        element: (
          <OwnerProtectedRoute>
            <PermissionsManager />
          </OwnerProtectedRoute>
        ),
      },
      {
        path: 'dms',
        element: <TaskDashboard />,
      },
      {
        path: 'dms/tasks/:id',
        element: <TaskDetail />,
      },
      {
        path: 'planning',
        element: <PlanningHub />,
      },
      {
        path: 'users',
        element: (
          <AdminProtectedRoute>
            <UserManagement />
          </AdminProtectedRoute>
        ),
      },
      {
        path: 'notifications',
        element: <NotificationsPage />,
      },
    ],
  },
]);

function App() {
  return <RouterProvider router={router} />;
}

export default App;
