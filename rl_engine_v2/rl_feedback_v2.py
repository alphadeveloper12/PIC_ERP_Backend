import torch
import torch.nn as nn
import torch.optim as optim
from sentence_transformers import SentenceTransformer
import pickle
import os
import json

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEVICE = "cpu"
MODEL_SAVE_PATH = os.path.join(BASE_DIR, "models/rl_erc_model.pth")
LABEL_ENCODERS_PATH = os.path.join(BASE_DIR, "models/label_encoders.pkl")
PRIMAVERA_LINKS_PATH = os.path.join(BASE_DIR, "models/primavera_links.json")
SBERT_MODEL_NAME = 'all-MiniLM-L6-v2'

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
        self.sbert_model = SentenceTransformer(SBERT_MODEL_NAME, device='cpu')

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
        
        self.agent.train()
        self.optimizer = optim.Adam(self.agent.parameters(), lr=0.0001)
        self.criterion = nn.CrossEntropyLoss()

        # Load Primavera Links
        self.primavera_links = {}
        if os.path.exists(PRIMAVERA_LINKS_PATH):
            try:
                with open(PRIMAVERA_LINKS_PATH, 'r') as f:
                    self.primavera_links = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load Primavera links: {e}")

        # Load Ground Truth Knowledge Base
        self.kb = {}
        self.kb_path = os.path.join(BASE_DIR, "models/knowledge_base.json")
        self.kb_embeddings = None
        self.kb_keys = []
        if os.path.exists(self.kb_path):
            try:
                with open(self.kb_path, 'r') as f:
                    self.kb = json.load(f)
                self.kb_keys = list(self.kb.keys())
                if self.kb_keys:
                    print(f"Pre-calculating KB embeddings for {len(self.kb_keys)} entries...")
                    self.kb_embeddings = self.sbert_model.encode(self.kb_keys, convert_to_tensor=True).to(DEVICE)
            except Exception as e:
                print(f"Warning: Could not load Knowledge Base: {e}")

    def find_kb_match(self, description, unit=None, threshold=0.75):
        """
        Finds the best match in the Knowledge Base using semantic similarity.
        Lowered threshold to 0.75 for better recall during debugging.
        """
        if self.kb_embeddings is None or not self.kb_keys:
            return None, 0.0

        from sentence_transformers import util
        
        desc_emb = self.sbert_model.encode([description.lower()], convert_to_tensor=True).to(DEVICE)
        cosine_scores = util.cos_sim(desc_emb, self.kb_embeddings)[0]
        best_score, best_idx = torch.max(cosine_scores, dim=0)
        
        if best_score.item() >= threshold:
            match_key = self.kb_keys[best_idx.item()]
            match_data = self.kb[match_key]
            
            # Unit simple validation
            final_score = best_score.item()
            if unit and match_data.get('unit'):
                u1 = str(unit).lower().replace('²', '2').replace('³', '3').strip()
                u2 = str(match_data['unit']).lower().replace('²', '2').replace('³', '3').strip()
                if u1 != u2 and u1 != "" and u2 != "":
                    final_score *= 0.8 # Penalty for unit mismatch
            
            return match_data, final_score
            
        return None, 0.0

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
        self.agent.train()
        if corrected_label not in self.label_to_idx:
            self._expand_model(corrected_label)
        target_idx = self.label_to_idx[corrected_label]
        target_tensor = torch.tensor([target_idx]).to(DEVICE)
        with torch.no_grad():
            embedding = self.sbert_model.encode([activity_name], convert_to_tensor=True).to(DEVICE)
        embedding = embedding.clone().detach().requires_grad_(True)
        self.optimizer.zero_grad()
        output = self.agent(embedding)
        loss = self.criterion(output, target_tensor)
        loss.backward()
        self.optimizer.step()
        torch.save(self.agent.state_dict(), MODEL_SAVE_PATH)

    def _expand_model(self, new_label):
        new_idx = len(self.unique_labels)
        self.unique_labels.append(new_label)
        self.label_to_idx[new_label] = new_idx
        self.idx_to_label[new_idx] = new_label
        with open(LABEL_ENCODERS_PATH, 'wb') as f:
            pickle.dump({
                'label_to_idx': self.label_to_idx,
                'idx_to_label': self.idx_to_label,
                'unique_labels': self.unique_labels
            }, f)
        old_layer = self.agent.network[-1]
        new_layer = nn.Linear(old_layer.in_features, len(self.unique_labels)).to(DEVICE)
        with torch.no_grad():
            new_layer.weight[:old_layer.out_features] = old_layer.weight
            new_layer.bias[:old_layer.out_features] = old_layer.bias
        self.agent.network[-1] = new_layer
        self.optimizer = optim.Adam(self.agent.parameters(), lr=0.0001)

    def update_primavera_link(self, boq_desc, prim_id):
        self.primavera_links[boq_desc] = prim_id
        try:
            os.makedirs(os.path.dirname(PRIMAVERA_LINKS_PATH), exist_ok=True)
            with open(PRIMAVERA_LINKS_PATH, 'w') as f:
                json.dump(self.primavera_links, f, indent=4)
        except Exception as e:
            print(f"Error saving Primavera links: {e}")

    def update_knowledge_base(self, boq_desc, erc_code=None, activities=None, unit=None):
        """
        Updates the Knowledge Base for a specific BOQ description.
        (NEW in v2)
        """
        key = boq_desc.lower().strip()
        if key not in self.kb:
            self.kb[key] = {"original_desc": boq_desc, "erc_code": "", "unit": "", "activities": []}
        
        if erc_code: self.kb[key]['erc_code'] = erc_code
        if unit: self.kb[key]['unit'] = unit
        if activities is not None:
            if isinstance(activities, str): activities = [activities]
            self.kb[key]['activities'] = list(set(activities)) # Deduplicate
            
        try:
            with open(self.kb_path, 'w') as f:
                json.dump(self.kb, f, indent=4)
            
            # Refresh embeddings
            self.kb_keys = list(self.kb.keys())
            if self.kb_keys:
                self.kb_embeddings = self.sbert_model.encode(self.kb_keys, convert_to_tensor=True).to(DEVICE)
            print(f"Knowledge Base updated for: '{boq_desc}'")
        except Exception as e:
            print(f"Error saving Knowledge Base: {e}")

if __name__ == "__main__":
    handler = RLFeedbackHandler()
    test_activity = "Installation of Access Control System"
    pred, conf = handler.predict(test_activity)
    print(f"Prediction: {pred} (Conf: {conf:.4f})")
