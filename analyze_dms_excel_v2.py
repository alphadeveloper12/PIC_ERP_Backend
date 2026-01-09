import pandas as pd
import os

file_path = '/home/ebony/PycharmProjects/PIC_ERP_Backend/assets/DMS workflow for PIC ERP.xlsx'

try:
    # Load the Excel file, skipping the first row which seems to be the main header "Tendering"
    # Actually, let's load with header=1 to get Seq, Actor, etc correctly if row 0 is the title
    df = pd.read_excel(file_path, header=1)
    
    print("Columns:", df.columns.tolist())
    
    # Check if 'Actor' column exists
    if 'Actor' in df.columns:
        print("\nUnique Actors:", df['Actor'].unique())
    
    # Group by the first column if it represents phases. 
    # The first column name from previous run was 'Tendering' but that was when header=0.
    # With header=1, the first column might be 'Seq' or unnamed if the title spanned.
    # Let's check the first few rows again with the new header
    print("\nHead with header=1:")
    print(df.head().to_string())
    
    # Let's try to infer phases. Often in these sheets, the phase is in a merged cell or specific column.
    # If the previous output showed 'Tendering' as the column name, it might be the only phase in that block?
    # Or maybe I should read without header and parse manually.
    
    print("\n--- Raw Data Analysis ---")
    df_raw = pd.read_excel(file_path, header=None)
    print(df_raw.head(10).to_string())
    
    # Detect potential phase headers (rows with only 1 non-null value or specific formatting?)
    # For now, let's just list all Actors and Receivers to get the Roles.
    
except Exception as e:
    print(f"Error reading Excel file: {e}")
