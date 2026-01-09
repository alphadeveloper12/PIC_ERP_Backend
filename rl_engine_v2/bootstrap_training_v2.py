import os
import sys
import pickle
import torch
import json

# Add project root to path to allow importing from sibling directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from rl_engine_v2.constants import ERC_MAP
# Import ERCAgent from the sibling module. 
# We need to make sure we don't trigger the __init__ of RLFeedbackHandler which raises the error.
from rl_engine_v2.rl_feedback_v2 import ERCAgent, MODEL_SAVE_PATH, LABEL_ENCODERS_PATH, DEVICE

def bootstrap_training():
    print("Bootstrapping RL Model...")
    
    # 1. Collect Unique Labels
    # We primarily get these from the ERC_MAP constant which defines the valid codes.
    unique_labels = sorted(list(set(ERC_MAP.values())))
    
    # Also check Knowledge Base if it exists, just in case there are extras (unlikely but good practice)
    kb_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models/knowledge_base.json")
    if os.path.exists(kb_path):
        try:
            with open(kb_path, 'r') as f:
                kb = json.load(f)
                for entry in kb.values():
                    code = entry.get('erc_code', '')
                    if code and code not in unique_labels:
                        unique_labels.append(code)
                        print(f"Added extra label from KB: {code}")
        except Exception as e:
            print(f"Warning reading KB: {e}")

    unique_labels = sorted(list(set(unique_labels)))
    print(f"Found {len(unique_labels)} unique labels.")

    # 2. Create Encoders
    label_to_idx = {label: idx for idx, label in enumerate(unique_labels)}
    idx_to_label = {idx: label for idx, label in enumerate(unique_labels)}

    encoders = {
        'label_to_idx': label_to_idx,
        'idx_to_label': idx_to_label,
        'unique_labels': unique_labels
    }

    # 3. Save Encoders
    os.makedirs(os.path.dirname(LABEL_ENCODERS_PATH), exist_ok=True)
    with open(LABEL_ENCODERS_PATH, 'wb') as f:
        pickle.dump(encoders, f)
    print(f"Saved encoders to {LABEL_ENCODERS_PATH}")

    # 4. Initialize and Save Model
    # Input dim for all-MiniLM-L6-v2 is 384
    input_dim = 384
    num_classes = len(unique_labels)
    
    agent = ERCAgent(input_dim, num_classes).to(DEVICE)
    
    # Save the initialized weights
    torch.save(agent.state_dict(), MODEL_SAVE_PATH)
    print(f"Saved initialized model to {MODEL_SAVE_PATH}")
    
    print("Bootstrap complete. RLFeedbackHandler should now work.")

if __name__ == "__main__":
    bootstrap_training()
