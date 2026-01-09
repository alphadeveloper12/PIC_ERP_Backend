import pandas as pd
import numpy as np
import re

def clean_text(text):
    if not isinstance(text, str):
        return ""
    # Remove special chars and extra spaces
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip().lower()

def clean_primavera_data_util(df):
    """
    Cleans Primavera P6 export data.
    Expected columns: Activity ID, Activity Name, Start, Finish, etc.
    """
    if df.empty:
        return df
    
    # Standardize column names
    df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
    
    # Ensure critical columns exist
    if 'activity_id' not in df.columns and 'activityid' in df.columns:
        df.rename(columns={'activityid': 'activity_id'}, inplace=True)
        
    if 'activity_name' not in df.columns and 'activityname' in df.columns:
        df.rename(columns={'activityname': 'activity_name'}, inplace=True)

    # fill na
    df.fillna('', inplace=True)
    return df

def clean_boq_data_util(df):
    """
    Cleans Bill of Quantities data.
    """
    if df.empty:
        return df
        
    df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
    
    # Common mappings
    rename_map = {
        'item': 'item_ref',
        'description': 'description',
        'unit': 'unit',
        'qty': 'quantity',
        'quantity': 'quantity',
        'rate': 'rate',
        'amount': 'amount'
    }
    
    for k, v in rename_map.items():
        if k in df.columns and v not in df.columns:
            df.rename(columns={k: v}, inplace=True)
            
    df.fillna(0, inplace=True)
    return df
