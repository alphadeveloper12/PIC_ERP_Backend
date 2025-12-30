import torch
import torch.nn as nn
import torch.optim as optim
from sentence_transformers import SentenceTransformer
import pickle
import os

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEVICE = "cpu"
MODEL_SAVE_PATH = os.path.join(BASE_DIR, "models/rl_erc_model.pth")
LABEL_ENCODERS_PATH = os.path.join(BASE_DIR, "models/label_encoders.pkl")
PRIMAVERA_LINKS_PATH = os.path.join(BASE_DIR, "models/primavera_links.json")
PRIMAVERA_NEGATIVE_LINKS_PATH = os.path.join(BASE_DIR, "models/primavera_negative_links.json")
SBERT_MODEL_NAME = 'all-MiniLM-L6-v2'
import json

class ERCAgent(nn.Module):
    def __init__(self, input_dim, num_classes):
        super(ERCAgent, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, 512),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, num_classes)
        )

    def forward(self, x):
        return self.network(x)

class RLFeedbackHandler:
    def __init__(self):
        # Load SBERT
        # self.sbert_model = SentenceTransformer(SBERT_MODEL_NAME)
        self.sbert_model = SentenceTransformer(SBERT_MODEL_NAME,device='cpu')

        # Load Encoders
        if not os.path.exists(LABEL_ENCODERS_PATH):
            raise FileNotFoundError("Label encoders not found. Run bootstrap training first.")
            
        with open(LABEL_ENCODERS_PATH, 'rb') as f:
            encoders = pickle.load(f)
            self.label_to_idx = encoders['label_to_idx']
            self.idx_to_label = encoders['idx_to_label']
            self.unique_labels = encoders['unique_labels']
            
        # Load Agent
        input_dim = 384
        num_classes = len(self.unique_labels)
        self.agent = ERCAgent(input_dim, num_classes).to(DEVICE)
        
        if os.path.exists(MODEL_SAVE_PATH):
            self.agent.load_state_dict(torch.load(MODEL_SAVE_PATH, map_location=DEVICE))
        
        self.agent.train() # Set to train mode for updates
        self.optimizer = optim.Adam(self.agent.parameters(), lr=0.0001) # Lower LR for fine-tuning
        self.criterion = nn.CrossEntropyLoss()

        # Load Primavera Links
        self.primavera_links = {}
        if os.path.exists(PRIMAVERA_LINKS_PATH):
            try:
                with open(PRIMAVERA_LINKS_PATH, 'r') as f:
                    self.primavera_links = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load Primavera links: {e}")

        self.primavera_negative_links = {}
        if os.path.exists(PRIMAVERA_NEGATIVE_LINKS_PATH):
            try:
                with open(PRIMAVERA_NEGATIVE_LINKS_PATH, 'r') as f:
                    self.primavera_negative_links = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load Primavera negative links: {e}")

    def predict(self, activity_name):
        self.agent.eval()
        with torch.no_grad():
            embedding = self.sbert_model.encode([activity_name], convert_to_tensor=True).to(DEVICE)
            output = self.agent(embedding)
            prob = torch.softmax(output, dim=1)
            conf, pred_idx = torch.max(prob, dim=1)
            
            pred_label = self.idx_to_label[pred_idx.item()]
            return pred_label, conf.item()

    def update_with_feedback(self, activity_name, corrected_label):
        """
        Performs a single online update step based on human correction.
        """
        self.agent.train()
        
        # If the corrected label is new, we need to expand the model (advanced case)
        # For now, we assume the label exists in our initial set.
        if corrected_label not in self.label_to_idx:
            print(f"New label detected: {corrected_label}. Expanding model...")
            self._expand_model(corrected_label)

        target_idx = self.label_to_idx[corrected_label]
        target_tensor = torch.tensor([target_idx]).to(DEVICE)
        
        # Ensure we don't use inference mode for the embedding if we want to backprop through the MLP
        with torch.no_grad():
            embedding = self.sbert_model.encode([activity_name], convert_to_tensor=True).to(DEVICE)
        
        # Clone to get a normal tensor that can be used in autograd
        embedding = embedding.clone().detach().requires_grad_(True)
        
        # Perform update
        self.optimizer.zero_grad()
        output = self.agent(embedding)
        loss = self.criterion(output, target_tensor)
        loss.backward()
        self.optimizer.step()
        
        # Save updated model
        torch.save(self.agent.state_dict(), MODEL_SAVE_PATH)
        print(f"Model updated with correction: {activity_name} -> {corrected_label}")

    def _expand_model(self, new_label):
        """
        Expands the output layer of the MLP to accommodate a new class.
        """
        # Update encoders
        new_idx = len(self.unique_labels)
        self.unique_labels.append(new_label)
        self.label_to_idx[new_label] = new_idx
        self.idx_to_label[new_idx] = new_label
        
        # Save updated encoders
        with open(LABEL_ENCODERS_PATH, 'wb') as f:
            pickle.dump({
                'label_to_idx': self.label_to_idx,
                'idx_to_label': self.idx_to_label,
                'unique_labels': self.unique_labels
            }, f)
            
        # Expand the last layer of the agent
        old_layer = self.agent.network[-1]
        new_layer = nn.Linear(old_layer.in_features, len(self.unique_labels)).to(DEVICE)
        
        # Copy old weights
        with torch.no_grad():
            new_layer.weight[:old_layer.out_features] = old_layer.weight
            new_layer.bias[:old_layer.out_features] = old_layer.bias
            
        # Replace the layer
        self.agent.network[-1] = new_layer
        self.optimizer = optim.Adam(self.agent.parameters(), lr=0.0001) # Re-init optimizer
        print(f"Model expanded to {len(self.unique_labels)} classes.")

    def update_with_shorthand(self, activity_name, shorthand_code):
        """
        Updates the model using a shorthand code like 'CN-IF'.
        """
        # Reverse map for shorthand to full name
        # We'll use the ERC_MAP from prepare_rl_dataset or link_boq_primavera_rl
        # For simplicity, let's define a local reverse map or use the existing unique_labels
        
        parts = shorthand_code.split('-')
        full_parts = []
        
        # This is a bit tricky because one shorthand can map to multiple full names if not careful
        # But we'll try to match segments
        for part in parts:
            for label in self.unique_labels:
                label_parts = label.split('|')
                # Check if this shorthand part exists in any of the full label segments
                # This requires a more robust mapping, but for now we'll use a simple lookup
                pass # Logic moved to apply_feedback.py for better control
        
        # Actually, it's better to just expect the full label or provide a clear mapping tool.
        # Let's implement the update logic in a dedicated script.
        pass

    def update_primavera_link(self, boq_desc, prim_id):
        """
        Updates the manual mapping for a BOQ description to a Primavera Activity ID.
        """
        self.primavera_links[boq_desc] = prim_id
        
        # Save updated links
        try:
            os.makedirs(os.path.dirname(PRIMAVERA_LINKS_PATH), exist_ok=True)
            with open(PRIMAVERA_LINKS_PATH, 'w') as f:
                json.dump(self.primavera_links, f, indent=4)
            print(f"Primavera link updated: {boq_desc} -> {prim_id}")
        except Exception as e:
            print(f"Error saving Primavera links: {e}")

    def update_primavera_negative_link(self, boq_desc, prim_id):
        """
        Adds a Primavera Activity ID to the negative list for a BOQ description.
        """
        if boq_desc not in self.primavera_negative_links:
            self.primavera_negative_links[boq_desc] = []
        
        if prim_id not in self.primavera_negative_links[boq_desc]:
            self.primavera_negative_links[boq_desc].append(prim_id)
            
            # Save updated links
            try:
                os.makedirs(os.path.dirname(PRIMAVERA_NEGATIVE_LINKS_PATH), exist_ok=True)
                with open(PRIMAVERA_NEGATIVE_LINKS_PATH, 'w') as f:
                    json.dump(self.primavera_negative_links, f, indent=4)
                print(f"Primavera negative link added: {boq_desc} -> {prim_id}")
            except Exception as e:
                print(f"Error saving Primavera negative links: {e}")

if __name__ == "__main__":
    # Simple test
    handler = RLFeedbackHandler()
    test_activity = "Installation of Access Control System"
    pred, conf = handler.predict(test_activity)
    print(f"Prediction: {pred} (Conf: {conf:.4f})")
    
    # Simulate feedback
    handler.update_with_feedback(test_activity, "Material|Material Order|Authorities Approval")
