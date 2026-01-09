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

def clean_boq_data_util(df_or_path):
    """
    Cleans the BOQ data from a file path and returns a cleaned DataFrame.
    """
    if isinstance(df_or_path, str):
        try:
            df = pd.read_excel(df_or_path, header=None)
        except Exception as e:
            print(f"Error reading BOQ file from path: {e}")
            return pd.DataFrame()
    else:
        df = df_or_path

    if df.empty:
        return df

    # Replace empty strings and whitespace with NaN
    df = df.replace(r'^\s*$', np.nan, regex=True)

    # Remove rows that are completely empty or all NaN
    df_cleaned = df.dropna(how='all')

    # Define garbage patterns
    garbage_patterns = [
        "Carried to Collection",
        "COLLECTION",
        "Total Brought Forward from Page No.",
        "Carried to Final Summary"
    ]

    # Filter out rows containing garbage patterns
    mask = df_cleaned.apply(lambda x: x.astype(str).str.contains('|'.join(garbage_patterns), case=False, na=False)).any(
        axis=1)
    df_cleaned = df_cleaned[~mask]

    return df_cleaned
