import pandas as pd
import json
import os
import sys

# Constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
KB_PATH = os.path.join(MODELS_DIR, "knowledge_base.json")

def import_ground_truth(csv_path):
    if not os.path.exists(csv_path):
        print(f"Error: File {csv_path} not found.")
        return

    print(f"Reading ground truth from {csv_path}...")
    # Read CSV, skip initial metadata rows if necessary, or just load and filter
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    # Filter out empty rows and header sections (SECTION B etc)
    # Based on the sample, items have ITEM numbers (A, B, C...) or specific descriptions
    # We want rows that have Primavera-ERC-CODE
    if 'Primavera-ERC-CODE' not in df.columns:
        print("Error: 'Primavera-ERC-CODE' column not found.")
        return

    valid_rows = df[df['Primavera-ERC-CODE'].notna()].copy()
    print(f"Found {len(valid_rows)} valid ground truth rows.")

    kb = {}
    
    # Check if existing KB exists
    if os.path.exists(KB_PATH):
        try:
            with open(KB_PATH, 'r') as f:
                kb = json.load(f)
            print(f"Loaded existing Knowledge Base with {len(kb)} entries.")
        except Exception as e:
            print(f"Warning: Could not load existing KB: {e}")

    # Process each row
    for _, row in valid_rows.iterrows():
        desc = str(row['DESCRIPTION']).strip()
        erc = str(row['Primavera-ERC-CODE']).strip()
        unit = str(row['UNIT']).strip() if pd.notna(row['UNIT']) else ""
        
        # Collect all activity names (Name 1 to Name 8)
        activities = []
        for i in range(1, 9):
            col_name = f'Primavera Activity Name {i}' if i == 1 else f'Activity Name {i}'
            if col_name in df.columns and pd.notna(row[col_name]):
                val = str(row[col_name]).strip()
                if val: activities.append(val)

        if desc and (erc or activities):
            # Key by description (normalized)
            key = desc.lower() 
            kb[key] = {
                "original_desc": desc,
                "erc_code": erc,
                "unit": unit,
                "activities": activities
            }

    # Save Knowledge Base
    os.makedirs(MODELS_DIR, exist_ok=True)
    with open(KB_PATH, 'w') as f:
        json.dump(kb, f, indent=4)
    
    print(f"Knowledge Base updated. Total entries: {len(kb)}")
    print(f"Saved to {KB_PATH}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 import_ground_truth.py path/to/ground_truth.csv")
    else:
        import_ground_truth(sys.argv[1])
