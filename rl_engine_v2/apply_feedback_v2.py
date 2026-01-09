import pandas as pd
from .rl_feedback_v2 import RLFeedbackHandler
import sys
import os

# ERC Reverse Mapping for RL training
# This maps the short codes (e.g., 'CV-SB') back to the full labels (e.g., 'Civil & Architectural|Structure Works|Super Structure')
# (Simplified map for demonstration - in production this should be complete)
ERC_CODE_TO_LABEL = {
    'CN-SB': 'Construction|Structure Works|Sub Structure',
    'CN-SF': 'Construction|Super Structure|Structure Works',
    'CN-IF': 'Construction|Internal Finishing|Work Execution',
    'CN-MSE': 'Construction|Mechanically Stabilized Earth|Work Execution',
    'CN-AR': 'Construction|Architectural|Work Execution'
}

def apply_feedback_v2(csv_path):
    if not os.path.exists(csv_path):
        print(f"Error: Feedback file {csv_path} not found.")
        return

    print(f"Loading feedback from {csv_path}...")
    df = pd.read_csv(csv_path)
    handler = RLFeedbackHandler()
    
    count = 0
    for idx, row in df.iterrows():
        boq_desc = str(row.get('BOQ Description', '')).strip()
        corrected_erc_code = str(row.get('Corrected ERC', '')).strip()
        corrected_prim_name = str(row.get('Corrected Primavera Activity Name', '')).strip()
        unit = str(row.get('Unit', '')).strip()

        if not boq_desc or boq_desc.lower() == 'nan':
            continue

        print(f"Processing correction for: '{boq_desc}'")

        # 1. Update Knowledge Base (Instant FCM Fix)
        # This ensures that next time this BOQ item (or a similar one) is linked,
        # it uses these specific expert-assigned values.
        activities = [corrected_prim_name] if corrected_prim_name and corrected_prim_name.lower() != 'nan' else None
        erc_to_save = corrected_erc_code if corrected_erc_code and corrected_erc_code.lower() != 'nan' else None
        unit_to_save = unit if unit and unit.lower() != 'nan' else None
        
        handler.update_knowledge_base(
            boq_desc, 
            erc_code=erc_to_save, 
            activities=activities, 
            unit=unit_to_save
        )

        # 2. Retrain RL Model (Predictive Learning)
        # If an ERC correction is provided, we tell the neural network to associate 
        # this description with that ERC category for future UNKNOWN items.
        if erc_to_save:
            # Try to find the full label for training
            # (In a real scenario, we'd have a more robust lookup here)
            full_label = ERC_CODE_TO_LABEL.get(erc_to_save)
            if full_label:
                handler.update_with_feedback(boq_desc, full_label)
                print(f"  RL Model retrained for ERC: {erc_to_save}")
            else:
                print(f"  Note: Could not find full training label for code {erc_to_save}. Skipping RL retraining.")

        # 3. Update Manual Link (Legacy Override)
        if corrected_prim_name and corrected_prim_name.lower() != 'nan':
            handler.update_primavera_link(boq_desc, corrected_prim_name)
        
        count += 1

    print(f"\nFeedback loop complete. {count} corrections applied to Knowledge Base and RL Model.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Default for testing
        test_csv = "inputs/manual_feedback.csv"
        if os.path.exists(test_csv):
            apply_feedback_v2(test_csv)
        else:
            print("Usage: python apply_feedback_v2.py <feedback_csv>")
    else:
        apply_feedback_v2(sys.argv[1])
