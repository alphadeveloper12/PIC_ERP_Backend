import pandas as pd
import numpy as np
import re
from .models import P6Activity
from dms.models import Department, Task, WorkflowStep
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

def read_file_robust(file_path, header=0):
    try:
        return pd.read_excel(file_path, header=header)
    except Exception:
        return pd.read_csv(file_path, header=header)

def clean_primavera_data_util(input_file_path):
    """
    Cleans Primavera P6 data from a file path and returns a cleaned DataFrame.
    """
    df = read_file_robust(input_file_path, header=0)

    # Identify Activity Name column
    activity_col = None
    for col in df.columns:
        if 'Activity Name' in str(col):
            activity_col = col
            break

    if not activity_col:
        # Fallback if specific column not found? 
        # User code says:
        if len(df.columns) > 1:
            activity_col = df.columns[1]
        else:
            return df

    # Remove rows where Activity Name is NaN or empty
    df_cleaned = df.dropna(subset=[activity_col])
    # Ensure string and strip
    df_cleaned = df_cleaned[df_cleaned[activity_col].astype(str).str.strip() != '']

    def normalize_activity(text):
        if not isinstance(text, str):
            text = str(text)
        if '-Block' in text:
            text = text.split('-Block')[0]
        if ' -GH-' in text:
            text = text.split(' -GH-')[0]
        text = re.split(r'-\d+BR', text)[0]
        text = re.sub(r'\d+', '#', text)
        return text.strip()

    df_cleaned['normalized_activity'] = df_cleaned[activity_col].apply(normalize_activity)
    df_deduped = df_cleaned.drop_duplicates(subset=['normalized_activity'], keep='first')
    df_deduped = df_deduped.drop(columns=['normalized_activity'])

    return df_deduped

def get_department_from_activity(activity_name: str):
    """
    Maps activity name to a Department Code using keywords.
    """
    name_lower = activity_name.lower()
    
    # Keyword Mappings
    if any(k in name_lower for k in ['noc', 'authority', 'authorities', 'approval', 'permit', 'utility', 'utilities']):
        return 'AUTH' # Authorities and Approvals
    elif any(k in name_lower for k in ['design', 'drawing', 'review', 'engineering', 'calculation', 'technical']):
        return 'ENG' # Engineering
    elif any(k in name_lower for k in ['procurement', 'ordering', 'material', 'supply', 'purchase', 'wiring accessories']):
        return 'PROC' # Procurement
    elif any(k in name_lower for k in ['construction', 'site', 'install', 'execution', 'mobiliz', 'civil', 'mep', 'finishing']):
        return 'CONST' # Construction/Site
    elif any(k in name_lower for k in ['handover', 'snag', 'closeout', 'commissioning']):
        return 'PJM' # Project Management / Handover
    
    return None

def import_primavera_data(file_path, primavera_sheet):
    """
    Imports P6 data, creates P6Activity, assigns Department, and creates DMS Task.
    """
    df = clean_primavera_data_util(file_path)
    
    created_count = 0
    updated_count = 0
    
    # Cache departments to avoid db hits
    dept_cache = {}
    
    # Helper to handle NaN/Nat
    def clean_val(val, default=None):
        if pd.isna(val) or val == '':
            return default
        return val

    # Determine columns dynamically
    cols = df.columns
    activity_id_col = next((c for c in cols if 'Activity ID' in str(c)), None)
    activity_name_col = next((c for c in cols if 'Activity Name' in str(c)), None)
    
    # If not found, try index 0 and 1 as fallback from user logic?
    if not activity_id_col and len(cols) > 0: activity_id_col = cols[0]
    if not activity_name_col and len(cols) > 1: activity_name_col = cols[1]

    if not activity_id_col:
        return {"error": "Activity ID column not found"}

    for _, row in df.iterrows():
        activity_id = str(row[activity_id_col]).strip()
        activity_name = str(row[activity_name_col]).strip() if activity_name_col else "Unknown"
        
        if not activity_id:
            continue
            
        defaults = {
            'activity_name': activity_name,
            'original_duration': clean_val(row.get('Original Duration')),
            'early_start': clean_val(row.get('Early Start')),
            'early_finish': clean_val(row.get('Early Finish')),
            'late_start': clean_val(row.get('Late Start')),
            'late_finish': clean_val(row.get('Late Finish')),
            'total_float': clean_val(row.get('Total Float')),
            'budgeted_total_cost': clean_val(row.get('Budgeted Total Cost')),
            'owner': clean_val(row.get('Owner')),
            'primavera_sheet': primavera_sheet
        }
        
        # 1. Determine Department
        dept_code = get_department_from_activity(activity_name)
        if not dept_code:
            dept_code = 'PJM' # Default to Project Management if unclassified
            
        if dept_code:
            if dept_code not in dept_cache:
                # Try to find department, if not found, maybe don't crash but skip? 
                # Or create a default one? ideally it should exist.
                dept_obj = Department.objects.filter(code=dept_code).first()
                if not dept_obj and dept_code == 'PJM':
                     # Fallback check if PJM exists, if not maybe 'ADMIN' or just skip
                     pass
                dept_cache[dept_code] = dept_obj
            
            if dept_cache.get(dept_code):
                defaults['department'] = dept_cache[dept_code]
        
        # 2. Update/Create P6Activity
        p6_activity, created = P6Activity.objects.update_or_create(
            activity_id=activity_id,
            primavera_sheet=primavera_sheet,
            defaults=defaults
        )
        
        if created:
            created_count += 1
        else:
            updated_count += 1
            
        # 3. Create DMS Task if Logic Applies
        from dms.models import WorkflowTemplate, DepartmentWorkflowMapping, WorkflowStep, Task
        
        # Only create if department is known and no task exists
        if p6_activity.department and not p6_activity.dms_task:
            # Logic: Find mapping for this department and activity ID
            template = None
            mappings = DepartmentWorkflowMapping.objects.filter(department=p6_activity.department).order_by('-priority')
            for mapping in mappings:
                if not mapping.activity_type_prefix or p6_activity.activity_id.startswith(mapping.activity_type_prefix):
                    template = mapping.template
                    break
            
            start_step = None
            if template:
                # Find the first step of the first phase in this template
                start_step = WorkflowStep.objects.filter(
                    phase__template=template,
                    is_start_step=True
                ).order_by('phase__sequence', 'ordering').first()
                if not start_step:
                    # Fallback to first step of template regardless of is_start_step
                    start_step = WorkflowStep.objects.filter(
                        phase__template=template
                    ).order_by('phase__sequence', 'ordering').first()
            
            if not start_step:
                # Legacy fallback: any start step for this department
                start_step = WorkflowStep.objects.filter(
                    actor_department=p6_activity.department, 
                    is_start_step=True
                ).first()
            
            if not start_step:
                # Extreme fallback: pick first step for department
                start_step = WorkflowStep.objects.filter(
                    actor_department=p6_activity.department
                ).order_by('phase__ordering' if hasattr(WorkflowStep, 'phase__ordering') else 'ordering').first()
            
            if start_step:
                # Find project (PrimaveraSheet has SubPhase, need Project link. 
                # SubPhase -> Project
                project = primavera_sheet.subphase.project
                
                # Check idempotency
                if not Task.objects.filter(linked_p6_activity=p6_activity).exists():
                    task = Task.objects.create(
                        project=project,
                        workflow_step=start_step,
                        status='PENDING',
                        assigned_to=None # HOD needs to assign
                    )
                    # Link back
                    p6_activity.dms_task = task
                    p6_activity.save()
                    print(f"DEBUG: Created task for P6 Activity {p6_activity.activity_id} (Step: {start_step.sequence_id})")

    return {
        "created": created_count,
        "updated": updated_count,
        "total": created_count + updated_count
    }
