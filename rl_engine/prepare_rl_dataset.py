import pandas as pd
import numpy as np
import re
import os

# ERC Code Mappings provided by the user
ERC_MAP = {
    'CL': 'Closeout',
    'CV': 'Civil & Architectural',
    'CN': 'Construction',
    'GEN': 'General Requirements',
    'MOS': 'Method of Statements',
    'SD': 'Shop Drawing',
    'AR': 'Architectural',
    'AD': 'Authority Drawings',
    'BP': 'Building Permits',
    'CM': 'Controlled Milestones',
    'DC': 'Documentation',
    'KM': 'Key Milestone',
    'ME': 'Material Order',
    'MT': 'Material',
    'PQN': 'Prequalification Number',
    'MB': 'Mobilization',
    'NO': 'No Objection Certificates (Authority approvals)',
    'MP': 'MEP related items',
    'SF': 'Super Structure',  # Note: Collision with Sanitary Fixtures & Accessories
    'ST': 'Structure',
    'PC': 'Procurement',
    'SB': 'Structure Works',
    'CA': 'Consultant Approval',
    'IF': 'Internal Finishing',
    'WE': 'Work Execution',
    'EL': 'Electrical Power & Lighting',
    'EF': 'External Finishes',
    'EW': 'External Works',
    'GS': 'Gas / LPG System',
    'HV': 'HVAC Systems Family',
    'MG': 'MEP General',
    'PD': 'Plumbing & Drainage Family',
    'SW': 'Structural Works',
    'BB': 'Balcony & Balustrade Works',
    'BW': 'Boundary Walls & Fencing',
    'BM': 'Builders Work for MEP',
    'DW': 'Doors & Windows',
    'DR': 'Drainage Works',
    'EP': 'Electrical Power Works',
    'EV': 'Elevation / Façade Works',
    'FT': 'Floor & Wall Tiling Works',
    'GC': 'Gypsum / Ceiling Works',
    'KC': 'Kitchen Units & Counters',
    'LG': 'LPG / Gas Works',
    'LW': 'Lighting Works',
    'NA': 'Not Applicable',
    'PW': 'Painting Works',
    'PL': 'Plaster Works',
    'SC': 'Screed Works',
    'TL': 'Tiling Works',
    'WT': 'Wall Tiling Works',
    'WC': 'Wardrobes & Closets',
    'WP': 'Waterproofing Works',
    'ATH': 'Authorities Inspection & Approval',
    'SN': 'Snagging by Consultant',
    'TC': 'Testing & Commisioning',
    'MSE': 'Mechanically Stabilized Earth',
    'AP': 'Authorities Approval',
    'PS': 'Project Signing',
    'DOC': 'Documentation',
    'NOC': 'No Objection Certificates',
    'CO': 'Close out Documentation'
}

def normalize_activity(text):
    if not isinstance(text, str):
        return str(text)
    
    # Remove specific junk substrings with more robust regex
    junk_patterns = [
        r'\[by others\]-GH-',
        r'-Block\s*\[.*?\]',
        r'-Block',
        r'\s*-GH-',
        r'-GH-',
        r'-?(\d+BR\d*-ST\d*)', # e.g., 4BR-ST2 or -4BR-ST2
        r'-?(\d+BR\d*)',      # e.g., 4BR or -4BR
        r'-?ST\d+',           # e.g., ST2 or -ST2
        r'-EX-',
        r'-RF-',
        r'-GF-',
        r'Mockup#\d+',
        r'-\d+BR\d*-',
        r'-Villa-',
        r'\[.*?\]',           # Remove any remaining bracketed text
    ]
    for pattern in junk_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Replace numbers with # as in the original util
    text = re.sub(r'\d+', '#', text)
    
    return text.strip()

def categorize_activity_id(activity_id):
    if not isinstance(activity_id, str):
        return pd.Series([None, None, None])
    
    parts = activity_id.split('-')
    # Skip the first part (Project Code like NH9)
    relevant_parts = parts[1:]
    
    categories = []
    for part in relevant_parts:
        # Try to map the code
        if part in ERC_MAP:
            categories.append(ERC_MAP[part])
        # If it's not in map and not numeric, it might be a sub-code we missed?
        # But for now we follow the user's mapping.
            
    # Return up to 3 levels of categorization
    cat1 = categories[0] if len(categories) > 0 else None
    cat2 = categories[1] if len(categories) > 1 else None
    cat3 = categories[2] if len(categories) > 2 else None
    
    return pd.Series([cat1, cat2, cat3])

def prepare_dataset(input_path, output_path):
    print(f"Loading data from {input_path}...")
    df = pd.read_excel(input_path, header=0)
    
    # Identify columns
    id_col = None
    name_col = None
    for col in df.columns:
        if 'Activity ID' in str(col):
            id_col = col
        if 'Activity Name' in str(col):
            name_col = col
            
    if not id_col or not name_col:
        # Fallback to index if names not found
        id_col = df.columns[0]
        name_col = df.columns[1]
        print(f"Warning: Columns not found by name. Using {id_col} and {name_col}")

    print(f"Initial rows: {len(df)}")
    
    # 1. Remove rows with NaN or empty values in ID or Name
    df = df.dropna(subset=[id_col, name_col])
    df = df[df[id_col].astype(str).str.strip() != '']
    df = df[df[name_col].astype(str).str.strip() != '']
    print(f"Rows after NaN/empty removal: {len(df)}")
    
    # 2. Normalize Activity Name and Remove Junk
    df['normalized_activity'] = df[name_col].apply(normalize_activity)
    
    # 3. Deduplicate based on normalized activity
    df = df.drop_duplicates(subset=['normalized_activity'], keep='first')
    print(f"Rows after deduplication: {len(df)}")
    
    # 4. Categorize based on Activity ID
    df[['Category', 'Subcategory', 'Detail_Category']] = df[id_col].apply(categorize_activity_id)
    
    # 5. Final cleanup and save
    # We keep the original ID and Name, plus the new categories and normalized name
    final_df = df[[id_col, name_col, 'normalized_activity', 'Category', 'Subcategory', 'Detail_Category']]
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    final_df.to_csv(output_path, index=False)
    print(f"Cleaned dataset saved to {output_path}")
    print(f"Final dataset size: {len(final_df)}")
    
    # Print some samples
    print("\nSample Categorization:")
    print(final_df.dropna(subset=['Category']).head(10).to_string())

if __name__ == "__main__":
    input_file = "inputs/primavera-p6.xlsx"
    output_file = "outputs/cleaned_training_dataset.csv"
    prepare_dataset(input_file, output_file)
