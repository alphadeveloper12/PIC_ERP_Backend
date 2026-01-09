import pandas as pd
import os

file_path = '/home/ebony/PycharmProjects/PIC_ERP_Backend/assets/DMS workflow for PIC ERP.xlsx'

try:
    # Load the Excel file
    xls = pd.ExcelFile(file_path)
    
    print(f"Sheet names: {xls.sheet_names}")
    
    for sheet_name in xls.sheet_names:
        print(f"\n--- Sheet: {sheet_name} ---")
        df = pd.read_excel(xls, sheet_name=sheet_name)
        print(df.head().to_string())
        print("\nColumns:", df.columns.tolist())
        print(f"Rows: {len(df)}")
        
except Exception as e:
    print(f"Error reading Excel file: {e}")
