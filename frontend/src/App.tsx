import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import ProjectSetup from './pages/admin/ProjectSetup';
import TeamManagement from './pages/owner/TeamManagement';
import TaskDashboard from './pages/dms/TaskDashboard';
import PrimaveraUpload from './pages/planning/PrimaveraUpload';
import P6ActivityManagement from './pages/planning/P6ActivityManagement';
import UserManagement from './pages/admin/UserManagement';
import { useAuthStore } from './hooks/useAuthStore';
import React from 'react';

// Protected Route Wrapper (Generic)
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { token } = useAuthStore();
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

// Admin Protected Route Wrapper (Superuser Only)
const AdminProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { token, user } = useAuthStore();

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  if (!user?.is_superuser) {
    return <Navigate to="/" replace />; // Redirect non-admins to dashboard
  }

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
        path: 'dms',
        element: <TaskDashboard />,
      },
      {
        path: 'planning/upload',
        element: <PrimaveraUpload />,
      },
      {
        path: 'planning/activities',
        element: <P6ActivityManagement />,
      },
      {
        path: 'users',
        element: (
          <AdminProtectedRoute>
            <UserManagement />
          </AdminProtectedRoute>
        ),
      },
    ],
  },
]);

function App() {
  return <RouterProvider router={router} />;
}

export default App;
