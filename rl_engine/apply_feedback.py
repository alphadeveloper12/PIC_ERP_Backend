import sys
from .rl_feedback_loop import RLFeedbackHandler

# Mapping of shorthand to full names (from our ERC_MAP)
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

def apply_correction(description, correct_shorthand):
    handler = RLFeedbackHandler()
    
    # Convert shorthand (e.g., CN-IF) to full label (e.g., Construction|Internal Finishing|)
    parts = correct_shorthand.split('-')
    full_names = []
    for part in parts:
        if part in SHORTHAND_TO_FULL:
            full_names.append(SHORTHAND_TO_FULL[part])
        else:
            print(f"Warning: Shorthand '{part}' not recognized. Skipping.")
            
    # Pad with empty strings to ensure 3 levels
    while len(full_names) < 3:
        full_names.append('')
        
    full_label = "|".join(full_names[:3])
    
    print(f"Applying correction:")
    print(f"  Description: {description}")
    print(f"  Shorthand:   {correct_shorthand}")
    print(f"  Full Label:  {full_label}")
    
    handler.update_with_feedback(description, full_label)
    print("Model updated successfully!")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 apply_feedback.py \"Activity Description\" \"CORRECT-SHORTHAND-CODE\"")
        print("Example: python3 apply_feedback.py \"To horizontal areas\" \"CN-IF\"")
    else:
        desc = sys.argv[1]
        code = sys.argv[2]
        apply_correction(desc, code)
