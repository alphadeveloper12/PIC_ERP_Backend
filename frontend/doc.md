# Frontend API Documentation

This document outlines the API endpoints used in the frontend, categorized by module and page, along with their purpose.

## Centralized Configuration
- **Base URL**: `http://localhost:8000`
- **Instance**: `src/services/api.ts` (Axios)
- **Authentication**: Bearer Token (JWT) managed in `src/hooks/useAuthStore.ts`.

---

## Authentication & Authorization
**File**: `src/hooks/useAuthStore.ts`

| Method | Endpoint | Purpose |
| :--- | :--- | :--- |
| `POST` | `/api/auth/login/` | User authentication and JWT token retrieval. |
| `POST` | `/api/auth/register/` | Global registration for new system users. |
| `GET` | `/api/auth/users/` | Fetching the list of all system users (Admin/Owner use). |

---

## Pages

### 1. Unified Dashboard
**File**: `src/pages/Dashboard.tsx`

| Method | Endpoint | Purpose |
| :--- | :--- | :--- |
| `GET` | `/dms/tasks/dashboard_stats/` | Retrieves metrics (Total, Completed, Pending) for the summary cards. |
| `GET` | `/dms/tasks/` | Fetches a short list of pending tasks requiring immediate attention. |

### 2. Task Registry (DMS)
**File**: `src/pages/dms/TaskDashboard.tsx`

| Method | Endpoint | Purpose |
| :--- | :--- | :--- |
| `GET` | `/dms/tasks/` | Main task listing (supports `mode` filters: `my_tasks`, `department`, `project_owner`). |
| `POST` | `/dms/tasks/` | Creating a custom task (ad-hoc assignment). |
| `POST` | `/dms/tasks/{id}/perform_action/` | Transitions task through workflow (START, SUBMIT, APPROVE, REJECT, ASSIGN). |
| `POST` | `/dms/documents/` | Uploading attachments/submissions for a specific task. |
| `GET` | `/api/project/list` | Fetching projects for the "Create Task" selection. |
| `GET` | `/dms/team/` | Fetching project-specific team members for task assignment. |

### 3. Team Management
**File**: `src/pages/owner/TeamManagement.tsx`

| Method | Endpoint | Purpose |
| :--- | :--- | :--- |
| `GET` | `/dms/team/` | Listing current project team members and their roles. |
| `POST` | `/dms/team/` | Assigning a system user to a specific project and department. |
| `GET` | `/dms/departments/` | Fetching available departments (Registry, Procurement, etc.). |
| `GET` | `/api/project/list` | Loading projects managed by the current Project Owner. |

### 4. Admin: Project Setup
**File**: `src/pages/admin/ProjectSetup.tsx`

| Method | Endpoint | Purpose |
| :--- | :--- | :--- |
| `GET` | `/api/project/list` | Listing all projects in the system. |
| `POST` | `/api/project/create` | Creating a new project and assigning an owner. |

### 5. Planning: Primavera Upload
**File**: `src/pages/planning/PrimaveraUpload.tsx`

| Method | Endpoint | Purpose |
| :--- | :--- | :--- |
| `POST` | `/planning/primavera-sheets/import_data/` | Uploading P6 Excel files and triggering task generation. |
| `GET` | `/api/subphase/list` | Fetching sub-phases (e.g. Tendering, Execution) for the selected project. |
| `POST` | `/api/subphase/create` | Creating a new sub-phase for a project. |

### 6. Planning: P6 Activity Registry
**File**: `src/pages/planning/P6ActivityManagement.tsx`

| Method | Endpoint | Purpose |
| :--- | :--- | :--- |
| `GET` | `/planning/p6-activities/` | Searchable listing of all P6 activities imported via sheet. |
| `POST` | `/planning/p6-activities/` | Manually creating a P6 activity. |
| `PUT` | `/planning/p6-activities/{id}/` | Updating existing P6 activity details. |
| `GET` | `/planning/primavera-sheets/` | Listing all uploaded Primavera sheets for filtering. |

### 7. Admin: User Management
**File**: `src/pages/admin/UserManagement.tsx`

| Method | Endpoint | Purpose |
| :--- | :--- | :--- |
| `GET` | `/api/auth/users/` | Master list of all system users with staff/superuser status. |
