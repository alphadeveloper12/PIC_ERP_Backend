import pandas as pd
import torch
from rl_feedback_loop import RLFeedbackHandler, DEVICE
import os

# ERC Reverse Mapping for code generation
ERC_MAP = {
    'Closeout': 'CL',
    'Civil & Architectural': 'CV',
    'Construction': 'CN',
    'General Requirements': 'GEN',
    'Method of Statements': 'MOS',
    'Shop Drawing': 'SD',
    'Architectural': 'AR',
    'Authority Drawings': 'AD',
    'Building Permits': 'BP',
    'Controlled Milestones': 'CM',
    'Documentation': 'DC',
    'Key Milestone': 'KM',
    'Material Order': 'ME',
    'Material': 'MT',
    'Prequalification Number': 'PQN',
    'Mobilization': 'MB',
    'No Objection Certificates (Authority approvals)': 'NO',
    'MEP related items': 'MP',
    'Super Structure': 'SF',
    'Structure': 'ST',
    'Procurement': 'PC',
    'Structure Works': 'SB',
    'Consultant Approval': 'CA',
    'Internal Finishing': 'IF',
    'Work Execution': 'WE',
    'Electrical Power & Lighting': 'EL',
    'External Finishes': 'EF',
    'External Works': 'EW',
    'Gas / LPG System': 'GS',
    'HVAC Systems Family': 'HV',
    'MEP General': 'MG',
    'Plumbing & Drainage Family': 'PD',
    'Structural Works': 'SW',
    'Balcony & Balustrade Works': 'BB',
    'Boundary Walls & Fencing': 'BW',
    'Builders Work for MEP': 'BM',
    'Doors & Windows': 'DW',
    'Drainage Works': 'DR',
    'Electrical Power Works': 'EP',
    'Elevation / Façade Works': 'EV',
    'Floor & Wall Tiling Works': 'FT',
    'Gypsum / Ceiling Works': 'GC',
    'Kitchen Units & Counters': 'KC',
    'LPG / Gas Works': 'LG',
    'Lighting Works': 'LW',
    'Not Applicable': 'NA',
    'Painting Works': 'PW',
    'Plaster Works': 'PL',
    'Screed Works': 'SC',
    'Tiling Works': 'TL',
    'Wall Tiling Works': 'WT',
    'Wardrobes & Closets': 'WC',
    'Waterproofing Works': 'WP',
    'Authorities Inspection & Approval': 'ATH',
    'Snagging by Consultant': 'SN',
    'Testing & Commisioning': 'TC',
    'Mechanically Stabilized Earth': 'MSE',
    'Authorities Approval': 'AP',
    'Project Signing': 'PS',
    'Documentation': 'DOC',
    'No Objection Certificates': 'NOC',
    'Close out Documentation': 'CO'
}

def predict_boq_erc(input_path, output_path):
    print(f"Loading BOQ from {input_path}...")
    # Load BOQ
    df = pd.read_excel(input_path)
    
    # Identify columns
    item_no_col = df.columns[0] # Usually the first column
    desc_col = 'Description' if 'Description' in df.columns else df.columns[1]
    
    print(f"Initial rows: {len(df)}")
    
    # 1. Cleanup: Remove completely empty rows (optional but keeps it clean)
    df = df.dropna(how='all')
    print(f"Rows after removing completely empty: {len(df)}")
    
    # 2. Identify BOQItems (rows where Item No is not empty)
    # We create a mask for items we want to predict
    item_mask = (df[item_no_col].astype(str).str.strip() != '') & (df[item_no_col].notna()) & (df[desc_col].notna())
    df_items = df[item_mask].copy()
    
    print(f"Items to predict: {len(df_items)}")
    
    if len(df_items) > 0:
        # 3. Initialize RL Handler
        handler = RLFeedbackHandler()
        
        # 4. Bulk Prediction
        print("Starting bulk prediction...")
        descriptions = df_items[desc_col].astype(str).tolist()
        
        with torch.no_grad():
            embeddings = handler.sbert_model.encode(descriptions, convert_to_tensor=True, show_progress_bar=True).to(DEVICE)
            handler.agent.eval()
            outputs = handler.agent(embeddings)
            probs = torch.softmax(outputs, dim=1)
            confs, pred_indices = torch.max(probs, dim=1)
            
        # Map indices back to labels
        predicted_labels = [handler.idx_to_label[idx.item()] for idx in pred_indices]
        confidences = [conf.item() for conf in confs]
        
        df_items['Predicted_ERC_Full'] = predicted_labels
        df_items['Confidence'] = confidences
        
        # Split into separate columns
        split_labels = df_items['Predicted_ERC_Full'].str.split('|', expand=True)
        df_items['Category'] = split_labels[0]
        df_items['Subcategory'] = split_labels[1]
        df_items['Detail_Category'] = split_labels[2]
        
        # 5. Generate Proper ERC Code
        def generate_erc_code(row, idx):
            cats = [row['Category'], row['Subcategory'], row['Detail_Category']]
            codes = []
            for cat in cats:
                if cat and cat in ERC_MAP:
                    codes.append(ERC_MAP[cat])
            
            code_str = "-".join(codes)
            if code_str:
                return f"{code_str}-{1000 + idx}"
            return f"UNK-{1000 + idx}"

        df_items['Proper_ERC_Code'] = [generate_erc_code(row, i) for i, row in enumerate(df_items.to_dict('records'))]
        
        # 6. Merge back to original dataframe
        # We initialize the new columns in the main df
        for col in ['Predicted_ERC_Full', 'Confidence', 'Category', 'Subcategory', 'Detail_Category', 'Proper_ERC_Code']:
            df[col] = None
            
        # Update the main df with the predicted values
        df.update(df_items)
    
    # 7. Save results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Predictions saved to {output_path}")
    
    # Print some samples
    print("\nSample Output (including non-predicted rows):")
    print(df[[item_no_col, desc_col, 'Proper_ERC_Code', 'Confidence']].head(20).to_string())

if __name__ == "__main__":
    input_file = "inputs/boq.xlsx"
    output_file = "outputs/boq_predictions.csv"
    predict_boq_erc(input_file, output_file)
