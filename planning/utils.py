import pandas as pd
import numpy as np
from .models import P6Activity
from rl_engine.data_processing import clean_primavera_data_util

def import_primavera_data(file_path, primavera_sheet):
    """
    Imports Primavera P6 data from an Excel file into the P6Activity model.
    Links activities to the provided PrimaveraSheet.
    """
    # Use the existing cleanup utility from rl_engine
    df = clean_primavera_data_util(file_path)
    
    created_count = 0
    updated_count = 0
    
    # Helper to handle NaN/Nat
    def clean_val(val, default=None):
        if pd.isna(val) or val == '':
            return default
        return val

    for _, row in df.iterrows():
        # Find the Activity ID column
        activity_id_col = None
        for col in df.columns:
            if 'Activity ID' in str(col):
                activity_id_col = col
                break
        
        if not activity_id_col:
             continue

        activity_id = str(row[activity_id_col]).strip()
        
        # Find other columns
        activity_name_col = next((c for c in df.columns if 'Activity Name' in str(c)), None)
        
        if not activity_id or not activity_name_col:
            continue

        activity_name = str(row[activity_name_col]).strip()
        
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
        
        obj, created = P6Activity.objects.update_or_create(
            activity_id=activity_id,
            primavera_sheet=primavera_sheet,
            defaults=defaults
        )
        
        if created:
            created_count += 1
        else:
            updated_count += 1
            
    return {
        "created": created_count,
        "updated": updated_count,
        "total": created_count + updated_count
    }
