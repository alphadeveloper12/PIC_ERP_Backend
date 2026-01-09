import pandas as pd
import torch
import numpy as np
from .rl_feedback_v2 import RLFeedbackHandler, DEVICE
from sentence_transformers import util
import os
import json
from tqdm import tqdm

# ERC Reverse Mapping for code generation (same as in predict_boq_erc.py)
ERC_MAP = {
    'Closeout': 'CL', 'Civil & Architectural': 'CV', 'Construction': 'CN',
    'General Requirements': 'GEN', 'Method of Statements': 'MOS', 'Shop Drawing': 'SD',
    'Architectural': 'AR', 'Authority Drawings': 'AD', 'Building Permits': 'BP',
    'Controlled Milestones': 'CM', 'Documentation': 'DC', 'Key Milestone': 'KM',
    'Material Order': 'ME', 'Material': 'MT', 'Prequalification Number': 'PQN',
    'Mobilization': 'MB', 'No Objection Certificates (Authority approvals)': 'NO',
    'MEP related items': 'MP', 'Super Structure': 'SF', 'Structure': 'ST',
    'Procurement': 'PC', 'Structure Works': 'SB', 'Consultant Approval': 'CA',
    'Internal Finishing': 'IF', 'Work Execution': 'WE', 'Electrical Power & Lighting': 'EL',
    'External Finishes': 'EF', 'External Works': 'EW', 'Gas / LPG System': 'GS',
    'HVAC Systems Family': 'HV', 'MEP General': 'MG', 'Plumbing & Drainage Family': 'PD',
    'Structural Works': 'SW', 'Balcony & Balustrade Works': 'BB', 'Boundary Walls & Fencing': 'BW',
    'Builders Work for MEP': 'BM', 'Doors & Windows': 'DW', 'Drainage Works': 'DR',
    'Electrical Power Works': 'EP', 'Elevation / Façade Works': 'EV', 'Floor & Wall Tiling Works': 'FT',
    'Gypsum / Ceiling Works': 'GC', 'Kitchen Units & Counters': 'KC', 'LPG / Gas Works': 'LG',
    'Lighting Works': 'LW', 'Not Applicable': 'NA', 'Painting Works': 'PW',
    'Plaster Works': 'PL', 'Screed Works': 'SC', 'Tiling Works': 'TL',
    'Wall Tiling Works': 'WT', 'Wardrobes & Closets': 'WC', 'Waterproofing Works': 'WP',
    'Authorities Inspection & Approval': 'ATH', 'Snagging by Consultant': 'SN',
    'Testing & Commisioning': 'TC', 'Mechanically Stabilized Earth': 'MSE',
    'Authorities Approval': 'AP', 'Project Signing': 'PS', 'Documentation': 'DOC',
    'No Objection Certificates': 'NOC', 'Close out Documentation': 'CO'
}

def clean_primavera_data(df, id_col, name_col):
    """
    Cleans Primavera data: removes NaN rows, garbage substrings, and deduplicates.
    """
    import re
    print("Cleaning Primavera data...")
    # 1. Remove rows where ID or Name is NaN
    df = df.dropna(subset=[id_col, name_col])
    df = df[df[name_col].astype(str).str.strip() != '']
    
    def normalize_activity(text):
        if not isinstance(text, str):
            return str(text)
        # Remove garbage patterns
        if '-Block' in text:
            text = text.split('-Block')[0]
        if ' -GH-' in text:
            text = text.split(' -GH-')[0]
        # Remove patterns like -4BR-ST2
        text = re.split(r'-\d+BR', text)[0]
        # Replace digits with # for deduplication purposes if needed, 
        # but here we just want to clean the name for better matching.
        return text.strip()
    
    df['Cleaned_Activity_Name'] = df[name_col].apply(normalize_activity)
    
    # 2. Deduplicate based on cleaned names
    original_len = len(df)
    df = df.drop_duplicates(subset=['Cleaned_Activity_Name'], keep='first')
    print(f"  Removed {original_len - len(df)} duplicate/garbage rows.")
    
    # Update the name column with cleaned name
    df[name_col] = df['Cleaned_Activity_Name']
    df = df.drop(columns=['Cleaned_Activity_Name'])
    
    return df

def link_boq_primavera(boq_path, primavera_path, output_path_csv, output_path_json):
    print(f"Loading BOQ from {boq_path}...")
    boq_df = pd.read_excel(boq_path)
    
    print(f"Loading Primavera from {primavera_path}...")
    prim_df = pd.read_excel(primavera_path)
    
    # Identify columns
    boq_item_no_col = boq_df.columns[0]
    boq_desc_col = 'Description' if 'Description' in boq_df.columns else boq_df.columns[1]
    
    prim_id_col = None
    prim_name_col = None
    for col in prim_df.columns:
        if 'Activity ID' in str(col): prim_id_col = col
        if 'Activity Name' in str(col): prim_name_col = col
    
    if not prim_id_col or not prim_name_col:
        prim_id_col, prim_name_col = prim_df.columns[0], prim_df.columns[1]

    # Clean Primavera Data
    prim_df = clean_primavera_data(prim_df, prim_id_col, prim_name_col)

    # 1. Clean BOQ and identify items to predict
    boq_df = boq_df.dropna(how='all')
    item_mask = (boq_df[boq_item_no_col].astype(str).str.strip() != '') & (boq_df[boq_item_no_col].notna()) & (boq_df[boq_desc_col].notna())
    boq_items = boq_df[item_mask].copy()
    
    print(f"BOQ Items to process: {len(boq_items)}")
    
    # 2. Initialize RL Handler and predict ERC for BOQ items
    handler = RLFeedbackHandler()
    print("Predicting ERC codes for BOQ items...")
    boq_descriptions = boq_items[boq_desc_col].astype(str).tolist()
    
    with torch.no_grad():
        embeddings = handler.sbert_model.encode(boq_descriptions, convert_to_tensor=True, show_progress_bar=True).to(DEVICE)
        handler.agent.eval()
        outputs = handler.agent(embeddings)
        probs = torch.softmax(outputs, dim=1)
        confs, pred_indices = torch.max(probs, dim=1)
        
    boq_items['Predicted_ERC_Full'] = [handler.idx_to_label[idx.item()] for idx in pred_indices]
    boq_items['prediction score'] = [conf.item() for conf in confs]
    
    # Split labels and generate proper ERC code
    split_labels = boq_items['Predicted_ERC_Full'].str.split('|', expand=True)
    boq_items['Category'] = split_labels[0]
    boq_items['Subcategory'] = split_labels[1]
    boq_items['Detail_Category'] = split_labels[2]
    
    def get_erc_codes(row):
        cats = [row['Category'], row['Subcategory'], row['Detail_Category']]
        return [ERC_MAP[c] for c in cats if c and c in ERC_MAP]

    boq_items['ERC_Codes'] = [get_erc_codes(row) for row in boq_items.to_dict('records')]
    boq_items['BOQ ERC-code'] = ["-".join(codes) for codes in boq_items['ERC_Codes']]

    # 3. Prepare Primavera Data
    # Pre-calculate embeddings for all Primavera activities
    print("Pre-calculating Primavera embeddings...")
    prim_names = prim_df[prim_name_col].astype(str).tolist()
    prim_embeddings = handler.sbert_model.encode(prim_names, convert_to_tensor=True, show_progress_bar=True).to(DEVICE)
    
    # 4. Linking Logic with Hierarchy and ERC Filtering
    print("Linking BOQ items to Primavera activities...")
    linked_data = []
    
    # JSON Root Structure
    json_root = {
        "id": 1,
        "name": "BOQ for Estimation",
        "sections": []
    }
    
    current_section = None
    current_subsection = None
    current_title = ""
    
    def get_section(name):
        for s in json_root['sections']:
            if s['name'] == name: return s
        new_s = {"id": len(json_root['sections']) + 100, "name": name, "subsections": []}
        json_root['sections'].append(new_s)
        return new_s

    def get_subsection(section, name):
        for s in section['subsections']:
            if s['name'] == name: return s
        new_s = {"id": len(section['subsections']) + 1000, "name": name, "items": []}
        section['subsections'].append(new_s)
        return new_s

    # Pre-calculate BOQ embeddings for all items to speed up
    item_indices = boq_items.index.tolist()
    
    for idx, row in tqdm(boq_df.iterrows(), total=len(boq_df), desc="Linking"):
        item_no = str(row[boq_item_no_col]).strip() if pd.notna(row[boq_item_no_col]) else ""
        desc = str(row[boq_desc_col]).strip() if pd.notna(row[boq_desc_col]) else ""
        
        is_item = item_no != "" and item_no.lower() != 'nan'
        
        if not is_item:
            # Update hierarchy
            if desc.upper().startswith("SECTION"):
                current_section = get_section(desc)
                current_subsection = None
                current_title = ""
            elif any(char.isdigit() for char in desc.split('-')[0]) and '-' in desc:
                if current_section is None: current_section = get_section("General Section")
                current_subsection = get_subsection(current_section, desc)
                current_title = ""
            elif desc != "":
                current_title = desc
            
            # Add header row to CSV output (kept for compatibility)
            full_row = {
                'Item No': item_no,
                'Description': desc,
                'Unit': row.get('Unit', ''),
                'Quantity': row.get('Quantity', ''),
                'Rate': row.get('Rate', ''),
                'Amount': row.get('Amount', ''),
                'BOQ ERC-code': '',
                'prediction score': '',
                'Primavera Activity Name 1': '',
                'Primavera Activity Id': '',
                'Score': '',
                'Original Duration': '',
                'Early Start': '',
                'Early Finish': '',
                'Late Start': '',
                'Late Finish': '',
                'Total Float': '',
                'Budgeted Total Cost': ''
            }
            linked_data.append(full_row)
            continue

        # Process Item
        boq_row = boq_items.loc[idx]
        combined_context = f"{current_title} {desc}".strip()
        erc_codes = boq_row['ERC_Codes']
        
        # Ensure structure for JSON
        if current_section is None: current_section = get_section("General Section")
        if current_subsection is None: current_subsection = get_subsection(current_section, "General Subsection")
        
        # 4.1 Check for manual link feedback
        manual_prim_id = handler.primavera_links.get(combined_context)
        
        matches = []
        
        if manual_prim_id:
            match_rows = prim_df[prim_df[prim_id_col].astype(str) == str(manual_prim_id)]
            if not match_rows.empty:
                best_prim_row = match_rows.iloc[0]
                matches.append({
                    'desc': best_prim_row[prim_name_col],
                    'ERC_code': best_prim_row[prim_id_col],
                    'Activity_ID': best_prim_row[prim_id_col],
                    'Original Duration': best_prim_row.get('Original Duration', ''),
                    'Early Start': str(best_prim_row.get('Early Start', '')),
                    'Early Finish': str(best_prim_row.get('Early Finish', '')),
                    'Late Start': str(best_prim_row.get('Late Start', '')),
                    'Late Finish': str(best_prim_row.get('Late Finish', '')),
                    'Total Float': best_prim_row.get('Total Float', ''),
                    'Budgeted Total Cost': best_prim_row.get('Budgeted Total Cost', ''),
                    'Score': 1.0
                })
                print(f"Using manual link for: {combined_context} -> {manual_prim_id}")
            else:
                print(f"Warning: Manual link ID {manual_prim_id} not found in Primavera data for {combined_context}")

        if not matches:
            # ERC Filtering: Match first level (e.g., 'CN')
            filtered_indices = []
            if erc_codes:
                target_erc_prefix = erc_codes[0] # e.g., 'CN'
                for p_idx, p_row in prim_df.iterrows():
                    p_id = str(p_row[prim_id_col])
                    p_id_parts = p_id.split('-')
                    # Check if target_erc_prefix is in any of the first 3 parts of Primavera ID
                    if any(target_erc_prefix == part for part in p_id_parts[:3]):
                        filtered_indices.append(prim_df.index.get_loc(p_idx))
            
            if filtered_indices:
                # Semantic matching with combined context
                with torch.no_grad():
                    context_emb = handler.sbert_model.encode([combined_context], convert_to_tensor=True).to(DEVICE)
                
                target_prim_embs = prim_embeddings[filtered_indices]
                cosine_scores = util.cos_sim(context_emb, target_prim_embs)[0]
                
                # Get Top 5 Matches
                top_k = min(5, len(filtered_indices))
                top_scores, top_indices_local = torch.topk(cosine_scores, k=top_k)
                
                for score, local_idx in zip(top_scores, top_indices_local):
                    global_idx = filtered_indices[local_idx.item()]
                    best_prim_row = prim_df.iloc[global_idx]
                    
                    # Helper to safe convert
                    def safe_val(val):
                        if pd.isna(val): return ""
                        if isinstance(val, (np.integer, np.int64)): return int(val)
                        if isinstance(val, (np.floating, np.float64, np.float32)): return float(val)
                        return val

                    matches.append({
                        'desc': str(best_prim_row[prim_name_col]),
                        'ERC_code': str(best_prim_row[prim_id_col]),
                        'Activity_ID': str(best_prim_row[prim_id_col]),
                        'Original Duration': safe_val(best_prim_row.get('Original Duration')),
                        'Early Start': str(best_prim_row.get('Early Start', '')),
                        'Early Finish': str(best_prim_row.get('Early Finish', '')),
                        'Late Start': str(best_prim_row.get('Late Start', '')),
                        'Late Finish': str(best_prim_row.get('Late Finish', '')),
                        'Total Float': safe_val(best_prim_row.get('Total Float')),
                        'Budgeted Total Cost': safe_val(best_prim_row.get('Budgeted Total Cost')),
                        'Score': round(score.item(), 4)
                    })
            
        # Add to JSON structure
        item_obj = {
            "id": int(idx) + 2000,
            "description": desc,
            "unit": str(row.get('Unit', '')),
            "quantity": str(row.get('Quantity', '')),
            "rate": str(row.get('Rate', '')),
            "amount": str(row.get('Amount', '')),
            "ERC_code": boq_row['BOQ ERC-code'],
            "primavera_activities": matches
        }
        current_subsection['items'].append(item_obj)

        # Add best match to CSV data
        if matches:
            best_match = matches[0]
            match_data = {
                'Primavera Activity Name 1': best_match['desc'],
                'Primavera Activity Id': best_match['Activity_ID'],
                'Score': best_match['Score'],
                'Original Duration': best_match['Original Duration'],
                'Early Start': best_match['Early Start'],
                'Early Finish': best_match['Early Finish'],
                'Late Start': best_match['Late Start'],
                'Late Finish': best_match['Late Finish'],
                'Total Float': best_match['Total Float'],
                'Budgeted Total Cost': best_match['Budgeted Total Cost']
            }
        else:
            match_data = {col: '' for col in ['Primavera Activity Name 1', 'Primavera Activity Id', 'Score', 'Original Duration', 'Early Start', 'Early Finish', 'Late Start', 'Late Finish', 'Total Float', 'Budgeted Total Cost']}
            
        full_row = {
            'Item No': item_no,
            'Description': desc,
            'Unit': row.get('Unit', ''),
            'Quantity': row.get('Quantity', ''),
            'Rate': row.get('Rate', ''),
            'Amount': row.get('Amount', ''),
            'BOQ ERC-code': boq_row['BOQ ERC-code'],
            'prediction score': round(boq_row['prediction score'], 4),
            **match_data
        }
        linked_data.append(full_row)

    # 5. Save to CSV
    output_df = pd.DataFrame(linked_data)
    cols = ['Item No', 'Description', 'Unit', 'Quantity', 'Rate', 'Amount', 'BOQ ERC-code', 
            'Primavera Activity Name 1', 'Primavera Activity Id', 'prediction score', 
            'Original Duration', 'Early Start', 'Early Finish', 'Late Start', 'Late Finish', 
            'Total Float', 'Budgeted Total Cost', 'Score']
    
    for col in cols:
        if col not in output_df.columns:
            output_df[col] = ''
            
    output_df = output_df[cols]
    
    os.makedirs(os.path.dirname(output_path_csv), exist_ok=True)
    output_df.to_csv(output_path_csv, index=False)
    print(f"Linked CSV data saved to {output_path_csv}")
    
    # 6. Save to JSON
    os.makedirs(os.path.dirname(output_path_json), exist_ok=True)
    with open(output_path_json, 'w') as f:
        json.dump(json_root, f, indent=4)
    print(f"Linked JSON data saved to {output_path_json}")

if __name__ == "__main__":
    # When running from within rl_engine, inputs and outputs are in the parent directory
    link_boq_primavera("../inputs/boq.xlsx", "../inputs/primavera-p6.xlsx", "../outputs/linked_boq_primavera_latest.csv", "../outputs/linked_boq_primavera.json")
