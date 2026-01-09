import pandas as pd
import torch
import numpy as np
from .rl_feedback_v2 import RLFeedbackHandler, DEVICE
from sentence_transformers import util
import os
import json
from tqdm import tqdm

# ERC Reverse Mapping for code generation
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
    import re
    print("Cleaning Primavera data...")
    df = df.dropna(subset=[id_col, name_col])
    df = df[df[name_col].astype(str).str.strip() != '']
    
    def normalize_activity(text):
        if not isinstance(text, str): return str(text)
        if '-Block' in text: text = text.split('-Block')[0]
        if ' -GH-' in text: text = text.split(' -GH-')[0]
        text = re.split(r'-\d+BR', text)[0]
        return text.strip()
    
    df['Cleaned_Activity_Name'] = df[name_col].apply(normalize_activity)
    original_len = len(df)
    df = df.drop_duplicates(subset=['Cleaned_Activity_Name'], keep='first')
    print(f"  Removed {original_len - len(df)} duplicate/garbage rows.")
    df[name_col] = df['Cleaned_Activity_Name']
    df = df.drop(columns=['Cleaned_Activity_Name'])
    return df

def link_boq_primavera_v2(boq_path, primavera_path, output_path_csv, output_path_json):
    print(f"Loading BOQ from {boq_path}...")
    boq_df = pd.read_excel(boq_path)
    
    print(f"Loading Primavera from {primavera_path}...")
    prim_df = pd.read_excel(primavera_path)
    
    boq_item_no_col = boq_df.columns[0]
    boq_desc_col = 'Description' if 'Description' in boq_df.columns else boq_df.columns[1]
    boq_unit_col = 'Unit' if 'Unit' in boq_df.columns else 'UNIT' # Handle variations
    
    prim_id_col, prim_name_col, prim_erc_col_name = None, None, None
    for col in prim_df.columns:
        if 'Activity ID' in str(col): prim_id_col = col
        if 'Activity Name' in str(col): prim_name_col = col
        if 'ERC_Code' in str(col) or 'ERC Code' in str(col): prim_erc_col_name = col
        
    if not prim_id_col or not prim_name_col:
        prim_id_col, prim_name_col = prim_df.columns[0], prim_df.columns[1]

    prim_df = clean_primavera_data(prim_df, prim_id_col, prim_name_col)

    boq_df = boq_df.dropna(how='all')
    item_mask = (boq_df[boq_item_no_col].astype(str).str.strip() != '') & (boq_df[boq_item_no_col].notna()) & (boq_df[boq_desc_col].notna())
    boq_items = boq_df[item_mask].copy()
    
    handler = RLFeedbackHandler()
    
    # Check if ERC codes are already provided in the BOQ dataframe
    if 'BOQ ERC-code' in boq_items.columns and boq_items['BOQ ERC-code'].notna().any():
        print("Using existing ERC codes for BOQ items...")
        if 'prediction score' not in boq_items.columns:
            boq_items['prediction score'] = 1.0
        
        # Fill missing ERC codes if any
        missing_mask = boq_items['BOQ ERC-code'].isna() | (boq_items['BOQ ERC-code'].astype(str).str.strip() == '')
        if missing_mask.any():
            print(f"  Predicting for {missing_mask.sum()} items with missing ERC codes...")
            missing_descriptions = boq_items.loc[missing_mask, boq_desc_col].astype(str).tolist()
            with torch.no_grad():
                embeddings = handler.sbert_model.encode(missing_descriptions, convert_to_tensor=True).to(DEVICE)
                handler.agent.eval()
                outputs = handler.agent(embeddings)
                probs = torch.softmax(outputs, dim=1)
                confs, pred_indices = torch.max(probs, dim=1)
            
            boq_items.loc[missing_mask, 'Predicted_ERC_Full'] = [handler.idx_to_label[idx.item()] for idx in pred_indices]
            boq_items.loc[missing_mask, 'prediction score'] = [conf.item() for conf in confs]
            
            # Helper to convert Predicted_ERC_Full to short code
            def full_to_short(full_label):
                parts = full_label.split('|')
                cats = [p for p in parts if p]
                codes = [ERC_MAP[c] for c in cats if c in ERC_MAP]
                return "-".join(codes)
            
            boq_items.loc[missing_mask, 'BOQ ERC-code'] = boq_items.loc[missing_mask, 'Predicted_ERC_Full'].apply(full_to_short)
        
        # Ensure ERC_Codes list exists for filtering
        def get_erc_codes_from_short(short_code):
            return str(short_code).split('-')
        
        boq_items['ERC_Codes'] = boq_items['BOQ ERC-code'].apply(get_erc_codes_from_short)

    else:
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
        
        split_labels = boq_items['Predicted_ERC_Full'].str.split('|', expand=True)
        boq_items['Category'] = split_labels[0]
        boq_items['Subcategory'] = split_labels[1]
        boq_items['Detail_Category'] = split_labels[2]
        
        def get_erc_codes(row):
            cats = [row['Category'], row['Subcategory'], row['Detail_Category']]
            return [ERC_MAP[c] for c in cats if c and c in ERC_MAP]

        boq_items['ERC_Codes'] = [get_erc_codes(row) for row in boq_items.to_dict('records')]
        boq_items['BOQ ERC-code'] = ["-".join(codes) for codes in boq_items['ERC_Codes']]

    print("Pre-calculating Primavera embeddings...")
    prim_names = prim_df[prim_name_col].astype(str).tolist()
    prim_embeddings = handler.sbert_model.encode(prim_names, convert_to_tensor=True, show_progress_bar=True).to(DEVICE)
    
    print("Linking BOQ items (v2 with FCM)...")
    linked_data = []
    json_root = {"id": 1, "name": "BOQ for Estimation", "sections": []}
    current_section, current_subsection, current_title = None, None, ""
    
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

    for idx, row in tqdm(boq_df.iterrows(), total=len(boq_df), desc="Linking"):
        item_no = str(row[boq_item_no_col]).strip() if pd.notna(row[boq_item_no_col]) else ""
        desc = str(row[boq_desc_col]).strip() if pd.notna(row[boq_desc_col]) else ""
        unit = str(row.get(boq_unit_col, '')).strip()
        
        is_item = item_no != "" and item_no.lower() != 'nan'
        
        if not is_item:
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
            
            full_row = {
                'Item No': item_no, 'Description': desc, 'Unit': unit,
                'Quantity': row.get('Quantity', ''), 'Rate': row.get('Rate', ''), 'Amount': row.get('Amount', ''),
                'BOQ ERC-code': '', 'prediction score': '', 'Primavera Activity Name 1': '',
                'Primavera Activity Id': '', 'Score': ''
            }
            linked_data.append(full_row)
            continue

        boq_row = boq_items.loc[idx]
        combined_context = f"{current_title} {desc}".strip()
        
        if current_section is None: current_section = get_section("General Section")
        if current_subsection is None: current_subsection = get_subsection(current_section, "General Subsection")
        
        matches = []
        final_erc = boq_row['BOQ ERC-code'] # Default to RL prediction
        
        # 4.1 Check Knowledge Base (FCM) - Dual Query Strategy
        # Try specific desc first, then combined context
        kb_match, kb_score = handler.find_kb_match(desc, unit=unit)
        if not kb_match:
            kb_match, kb_score = handler.find_kb_match(combined_context, unit=unit)
        
        if kb_match:
            # KB found something!
            kb_activities = kb_match.get('activities', [])
            kb_erc = kb_match.get('erc_code', '')
            if kb_erc: final_erc = kb_erc # KB Priority Override
            
            # Helper to normalize for comparison
            def norm_cmp(t):
                import re
                t = str(t).lower()
                t = re.sub(r'\[.*?\]', '', t) # Remove [P019] etc
                t = re.sub(r'type \w+-', '', t) # Remove Type 4A- etc
                return t.strip()

            norm_kb_acts = [norm_cmp(a) for a in kb_activities]
            
            # 1. Try to find these activities in the actual Primavera data (Normalized Match)
            for p_idx, p_row in prim_df.iterrows():
                p_name_norm = norm_cmp(p_row[prim_name_col])
                if p_name_norm in norm_kb_acts:
                    matches.append({
                        'desc': str(p_row[prim_name_col]),
                        'Activity_ID': str(p_row[prim_id_col]),
                        'ERC_code': str(p_row[prim_erc_col_name]) if prim_erc_col_name else 'N/A',
                        'Score': round(kb_score, 4),
                        'Source': 'Knowledge Base (Name Match)'
                    })
            
            # 2. If still no matches but we have an ERC, prioritize activities in that ERC (Hierarchical)
            if not matches and kb_erc:
                kb_erc_parts = kb_erc.split('-')
                filtered_indices = []
                
                for level in range(len(kb_erc_parts), 0, -1):
                    prefix = "-".join(kb_erc_parts[:level]).upper()
                    temp_filtered = []
                    
                    if prim_erc_col_name:
                        for p_idx, p_row in prim_df.iterrows():
                            p_erc = str(p_row[prim_erc_col_name]).strip().upper()
                            if p_erc == prefix or p_erc.startswith(prefix + "-"):
                                temp_filtered.append(prim_df.index.get_loc(p_idx))
                    
                    if not temp_filtered:
                        for p_idx, p_row in prim_df.iterrows():
                            p_id = str(p_row[prim_id_col]).upper()
                            p_parts = p_id.split('-')
                            if all(p in p_parts for p in kb_erc_parts[:level]):
                                temp_filtered.append(prim_df.index.get_loc(p_idx))
                    
                    if temp_filtered:
                        filtered_indices = temp_filtered
                        break
                
                if filtered_indices:
                    with torch.no_grad():
                        # Use combined context for fallback semantic match quality
                        context_emb = handler.sbert_model.encode([combined_context], convert_to_tensor=True).to(DEVICE)
                    target_prim_embs = prim_embeddings[filtered_indices]
                    cosine_scores = util.cos_sim(context_emb, target_prim_embs)[0]
                    top_k = min(3, len(filtered_indices))
                    top_scores, top_indices_local = torch.topk(cosine_scores, k=top_k)
                    
                    for score, local_idx in zip(top_scores, top_indices_local):
                        global_idx = filtered_indices[local_idx.item()]
                        p_row = prim_df.iloc[global_idx]
                        matches.append({
                            'desc': str(p_row[prim_name_col]),
                            'Activity_ID': str(p_row[prim_id_col]),
                            'ERC_code': str(p_row[prim_erc_col_name]) if prim_erc_col_name else 'N/A',
                            'Score': round(score.item(), 4),
                            'Source': 'Knowledge Base (ERC Fallback)'
                        })

        if not matches:
            # Fallback to pure Semantic Match with ERC Filtering
            erc_codes = boq_row['ERC_Codes']
            filtered_indices = []
            
            if erc_codes:
                target_parts = [str(c).strip().upper() for c in erc_codes if c]
                
                # Hierarchical filtering: try to match as many parts as possible, from full to prefix
                for level in range(len(target_parts), 0, -1):
                    prefix = "-".join(target_parts[:level])
                    
                    temp_filtered = []
                    if prim_erc_col_name:
                        for p_idx, p_row in prim_df.iterrows():
                            p_erc = str(p_row[prim_erc_col_name]).strip().upper()
                            # Match the prefix hierarchicaly
                            if p_erc == prefix or p_erc.startswith(prefix + "-"):
                                temp_filtered.append(prim_df.index.get_loc(p_idx))
                    
                    # If nothing in ERC column, fallback to Activity ID logic for this prefix
                    if not temp_filtered:
                        for p_idx, p_row in prim_df.iterrows():
                            p_id = str(p_row[prim_id_col]).upper()
                            p_id_parts = p_id.split('-')
                            # Check if prefix parts match any parts in P6 ID (simplified search)
                            if all(p in p_id_parts for p in target_parts[:level]):
                                temp_filtered.append(prim_df.index.get_loc(p_idx))
                    
                    if temp_filtered:
                        filtered_indices = temp_filtered
                        # Found some matches at this specific level of hierarchy, stop searching
                        # This ensures CN-PRE-GEN-GEN matches are preferred over CN-PRE
                        break
            
            # Universal fallback: if still no filtered indices, search everything
            if not filtered_indices:
                filtered_indices = list(range(len(prim_df)))

            if filtered_indices:
                with torch.no_grad():
                    context_emb = handler.sbert_model.encode([combined_context], convert_to_tensor=True).to(DEVICE)
                target_prim_embs = prim_embeddings[filtered_indices]
                cosine_scores = util.cos_sim(context_emb, target_prim_embs)[0]
                top_k = min(5, len(filtered_indices))
                top_scores, top_indices_local = torch.topk(cosine_scores, k=top_k)
                
                for score, local_idx in zip(top_scores, top_indices_local):
                    global_idx = filtered_indices[local_idx.item()]
                    best_prim_row = prim_df.iloc[global_idx]
                    matches.append({
                        'desc': str(best_prim_row[prim_name_col]),
                        'Activity_ID': str(best_prim_row[prim_id_col]),
                        'ERC_code': str(best_prim_row[prim_erc_col_name]) if prim_erc_col_name else 'N/A',
                        'Score': round(score.item(), 4),
                        'Source': 'SBERT Semantic (Filtered)' if filtered_indices != list(range(len(prim_df))) else 'SBERT Semantic (Unfiltered)'
                    })
            
        # Add to JSON
        item_obj = {
            "id": int(idx) + 2000, "description": desc, "unit": unit,
            "quantity": str(row.get('Quantity', '')), "rate": str(row.get('Rate', '')),
            "amount": str(row.get('Amount', '')), "ERC_code": final_erc,
            "primavera_activities": matches
        }
        current_subsection['items'].append(item_obj)

        # Add to CSV
        best_match = matches[0] if matches else {'desc': '', 'Activity_ID': '', 'Score': ''}
        full_row = {
            'Item No': item_no, 'Description': desc, 'Unit': unit,
            'Quantity': row.get('Quantity', ''), 'Rate': row.get('Rate', ''), 'Amount': row.get('Amount', ''),
            'BOQ ERC-code': final_erc, 'prediction score': round(boq_row['prediction score'], 4),
            'Primavera Activity Name 1': best_match.get('desc', ''),
            'Primavera Activity Id': best_match.get('Activity_ID', ''),
            'Score': best_match.get('Score', '')
        }
        linked_data.append(full_row)

    output_df = pd.DataFrame(linked_data)
    os.makedirs(os.path.dirname(output_path_csv), exist_ok=True)
    output_df.to_csv(output_path_csv, index=False)
    with open(output_path_json, 'w') as f:
        json.dump(json_root, f, indent=4)
    print(f"v2 Linked data saved to {output_path_csv} and {output_path_json}")
    return json_root

if __name__ == "__main__":
    link_boq_primavera_v2("inputs/boq.xlsx", "inputs/primavera-p6.xlsx", "outputs/linked_v2.csv", "outputs/linked_v2.json")
