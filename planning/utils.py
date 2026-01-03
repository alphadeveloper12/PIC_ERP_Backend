import pandas as pd
import numpy as np
from .models import P6Activity
from rl_engine.data_processing import clean_primavera_data_util
from .services.erc_model import ERCModel

def import_primavera_data(file_path, primavera_sheet):
    """
    Imports Primavera P6 data from an Excel file into the P6Activity model.
    Links activities to the provided PrimaveraSheet.
    """
    # Use the existing cleanup utility from rl_engine
    df = clean_primavera_data_util(file_path)
    
    # Initialize ERC Model
    erc_model = ERCModel()
    erc_model.load_model()
    
    created_count = 0
    updated_count = 0
    
    # Helper to handle NaN/Nat
    def clean_val(val, default=None):
        if pd.isna(val) or val == '':
            return default
        return val

    for _, row in df.iterrows():
        # Find the Activity ID and ERC Code columns
        activity_id_col = None
        erc_code_col = None
        for col in df.columns:
            if 'Activity ID' in str(col):
                activity_id_col = col
            if 'ERC_Code' in str(col) or 'ERC Code' in str(col):
                erc_code_col = col
        
        if not activity_id_col:
             continue

        activity_id = str(row[activity_id_col]).strip()
        
        # Find other columns
        activity_name_col = next((c for c in df.columns if 'Activity Name' in str(c)), None)
        
        if not activity_id or not activity_name_col:
            continue

        activity_name = str(row[activity_name_col]).strip()

        # Determine ERC Code
        if erc_code_col and pd.notna(row[erc_code_col]):
            erc_code = str(row[erc_code_col]).strip()
        else:
            # Use ML/Rule-based model to predict ERC Code
            predicted_codes = erc_model.predict([activity_name])
            erc_code = predicted_codes[0] if predicted_codes else activity_id
        
        defaults = {
            'activity_name': activity_name,
            'erc_code': erc_code,
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
