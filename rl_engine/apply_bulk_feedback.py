import pandas as pd
import sys
import os
from .rl_feedback_loop import RLFeedbackHandler

# Mapping of shorthand to full names (same as in apply_feedback.py)
SHORTHAND_TO_FULL = {
    'CL': 'Closeout', 'CV': 'Civil & Architectural', 'CN': 'Construction',
    'GEN': 'General Requirements', 'MOS': 'Method of Statements', 'SD': 'Shop Drawing',
    'AR': 'Architectural', 'AD': 'Authority Drawings', 'BP': 'Building Permits',
    'CM': 'Controlled Milestones', 'DC': 'Documentation', 'KM': 'Key Milestone',
    'ME': 'Material Order', 'MT': 'Material', 'PQN': 'Prequalification Number',
    'MB': 'Mobilization', 'NO': 'No Objection Certificates (Authority approvals)',
    'MP': 'MEP related items', 'SF': 'Super Structure', 'ST': 'Structure',
    'PC': 'Procurement', 'SB': 'Structure Works', 'CA': 'Consultant Approval',
    'IF': 'Internal Finishing', 'WE': 'Work Execution', 'EL': 'Electrical Power & Lighting',
    'EF': 'External Finishes', 'EW': 'External Works', 'GS': 'Gas / LPG System',
    'HV': 'HVAC Systems Family', 'MG': 'MEP General', 'PD': 'Plumbing & Drainage Family',
    'SW': 'Structural Works', 'BB': 'Balcony & Balustrade Works', 'BW': 'Boundary Walls & Fencing',
    'BM': 'Builders Work for MEP', 'DW': 'Doors & Windows', 'DR': 'Drainage Works',
    'EP': 'Electrical Power Works', 'EV': 'Elevation / Façade Works', 'FT': 'Floor & Wall Tiling Works',
    'GC': 'Gypsum / Ceiling Works', 'KC': 'Kitchen Units & Counters', 'LG': 'LPG / Gas Works',
    'LW': 'Lighting Works', 'NA': 'Not Applicable', 'PW': 'Painting Works',
    'PL': 'Plaster Works', 'SC': 'Screed Works', 'TL': 'Tiling Works',
    'WT': 'Wall Tiling Works', 'WC': 'Wardrobes & Closets', 'WP': 'Waterproofing Works',
    'ATH': 'Authorities Inspection & Approval', 'SN': 'Snagging by Consultant',
    'TC': 'Testing & Commisioning', 'MSE': 'Mechanically Stabilized Earth',
    'AP': 'Authorities Approval', 'PS': 'Project Signing', 'DOC': 'Documentation',
    'NOC': 'No Objection Certificates', 'CO': 'Close out Documentation'
}

def apply_bulk_feedback(csv_path):
    if not os.path.exists(csv_path):
        print(f"Error: File {csv_path} not found.")
        return

    print(f"Loading feedback from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    # Expected columns: 'Description' and 'Correct_Shorthand'
    if 'Description' not in df.columns or 'Correct_Shorthand' not in df.columns:
        print("Error: CSV must contain 'Description' and 'Correct_Shorthand' columns.")
        return

    handler = RLFeedbackHandler()
    
    print(f"Applying {len(df)} corrections...")
    for idx, row in df.iterrows():
        desc = str(row['Description'])
        shorthand = str(row['Correct_Shorthand'])
        
        # Convert shorthand to full label
        parts = shorthand.split('-')
        full_names = []
        for part in parts:
            if part in SHORTHAND_TO_FULL:
                full_names.append(SHORTHAND_TO_FULL[part])
        
        while len(full_names) < 3:
            full_names.append('')
            
        full_label = "|".join(full_names[:3])
        
        # Update model
        handler.update_with_feedback(desc, full_label)
        
        if (idx + 1) % 10 == 0:
            print(f"Processed {idx + 1}/{len(df)} corrections...")

    print("Bulk update complete! Model has been updated and saved.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 apply_bulk_feedback.py path/to/feedback.csv")
        print("CSV Format: Description,Correct_Shorthand")
    else:
        apply_bulk_feedback(sys.argv[1])
