# 🏗️ PIC ERP Backend (Django + DRF)

A modern, role-based ERP system designed for **construction companies**, built with **Django REST Framework**.  
This system models a complete organization: **Companies → Departments → Roles → Permissions → Employees → User Access**.

---

## 🚀 Overview

This ERP backend helps construction firms manage internal structure and access levels — from corporate offices to project sites.  
It supports multi-company operations, location-based roles, and approval hierarchies.

### Core Concepts

| Concept | Description |
|----------|--------------|
| **Company** | Represents a legal entity (e.g., PIC Contracting LLC). |
| **Location** | Physical site — HQ, site office, or regional branch. |
| **Department** | Division like Engineering, Procurement, or QA/QC. |
| **Grade** | Hierarchical rank (Engineer → Sr. Engineer → Manager). |
| **Job Family / Title** | HR classification and designations. |
| **Role** | Defines a set of permissions (e.g., Procurement Manager). |
| **Permission** | Specific allowed actions (e.g., approve PO). |
| **Employee** | A user profile linked to position and grade. |
| **UserRole** | Connects user ↔ department ↔ role (RBAC). |

---

## 🧩 System Flow

```mermaid
graph TD
    A[Company Registration] --> B[Add Locations]
    B --> C[Create Departments]
    C --> D[Define Job Families, Grades, Job Titles]
    D --> E[Setup Roles & Permissions]
    E --> F[Register Employees]
    F --> G[Assign Roles to Users]
    G --> H[Test Access /auth/me]
    H --> I[Extend: Projects, Approvals, Finance Modules]

🛠️ Setup Instructions
1. Clone & Install
git clone https://github.com/yourname/pic_erp_backend.git
cd pic_erp_backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

2. Apply Migrations
python manage.py migrate

3. Load Sample Data (Fixtures)

Recommended load order:

python manage.py loaddata fixtures/companies.json
python manage.py loaddata fixtures/locations.json
python manage.py loaddata fixtures/grades.json
python manage.py loaddata fixtures/job_families.json
python manage.py loaddata fixtures/departments.json
python manage.py loaddata fixtures/job_titles.json
python manage.py loaddata fixtures/permissions.json
python manage.py loaddata fixtures/roles.json
python manage.py loaddata fixtures/role_permissions.json


Each file corresponds to the logical setup order:
Company → Departments → Roles → Permissions → Role Mappings

🔑 Authentication
JWT (Recommended)

Install:

pip install djangorestframework-simplejwt


Add to settings.py:

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
}


Include URLs:

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/core/", include("core.urls", namespace="core")),
]

🔄 Step-by-Step Usage
🥇 Step 1 — Register a Company

POST /api/core/companies/create/

{
  "name": "Prime Infrastructure Contracting LLC",
  "code": "PIC-DXB",
  "address": "Dubai, UAE"
}

🏢 Step 2 — Add Locations

POST /api/core/locations/create/

{
  "name": "Head Office",
  "country": "UAE",
  "city": "Dubai"
}

🧭 Step 3 — Create Departments

POST /api/core/departments/create/

{
  "name": "Procurement",
  "description": "Material Purchase and Vendor Management"
}

👔 Step 4 — Define Job Families / Grades / Titles

Create job hierarchy through:

/api/core/job-families/create/

/api/core/grades/create/

/api/core/job-titles/create/

🧑‍💼 Step 5 — Add Roles and Permissions
POST /api/core/permissions/create/
{
  "code": "approve_po",
  "description": "Can approve purchase orders"
}


Then create a role:

POST /api/core/roles/create/
{
  "name": "Procurement Manager",
  "department": 5,
  "description": "Responsible for material approval workflow"
}


Assign permissions:

POST /api/core/roles/assign-permissions/
{
  "role_id": 5,
  "permission_codes": ["approve_po", "create_pr_po"]
}

👨‍🔧 Step 6 — Register Employees

POST /api/core/employees/create/

{
  "user": 5,
  "company": 1,
  "position": 3,
  "grade": 4,
  "first_name": "Ali",
  "last_name": "Mughal",
  "nationality": "Pakistan",
  "hire_date": "2025-02-01",
  "work_location": 2
}

👥 Step 7 — Assign Roles to Users

POST /api/core/user-roles/assign/

{
  "user": 5,
  "department": 3,
  "role": 2
}

✅ Step 8 — Test Permissions

GET /api/core/auth/me/

Example Response:

{
  "id": 5,
  "username": "ali.mughal",
  "departments": [
    {
      "name": "Procurement",
      "roles": [
        {
          "role_name": "Procurement Manager",
          "permissions": ["approve_po", "create_pr_po"]
        }
      ]
    }
  ]
}