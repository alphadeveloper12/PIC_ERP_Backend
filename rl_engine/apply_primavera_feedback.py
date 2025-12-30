import pandas as pd
import sys
import os
from .rl_feedback_loop import RLFeedbackHandler

def apply_primavera_feedback(csv_path):
    if not os.path.exists(csv_path):
        print(f"Error: File {csv_path} not found.")
        return

    print(f"Loading Primavera feedback from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    # Expected columns: 'Title', 'Description' and 'Correct_Activity_ID'
    if 'Title' not in df.columns or 'Description' not in df.columns or 'Correct_Activity_ID' not in df.columns:
        print("Error: CSV must contain 'Title', 'Description' and 'Correct_Activity_ID' columns.")
        return

    handler = RLFeedbackHandler()
    
    print(f"Applying {len(df)} Primavera link corrections...")
    for idx, row in df.iterrows():
        title = str(row['Title']).strip() if pd.notna(row['Title']) else ""
        desc = str(row['Description']).strip() if pd.notna(row['Description']) else ""
        prim_id = str(row['Correct_Activity_ID']).strip()
        
        # Combine context
        combined_context = f"{title} {desc}".strip()
        
        # Update mapping
        handler.update_primavera_link(combined_context, prim_id)
        
        if (idx + 1) % 10 == 0:
            print(f"Processed {idx + 1}/{len(df)} corrections...")

    print("Primavera feedback update complete!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 apply_primavera_feedback.py path/to/feedback.csv")
        print("CSV Format: Title,Description,Correct_Activity_ID")
    else:
        apply_primavera_feedback(sys.argv[1])
