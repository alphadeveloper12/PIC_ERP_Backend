import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sentence_transformers import SentenceTransformer
import os
import pickle

# Configuration
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_SAVE_PATH = "models/rl_erc_model.pth"
LABEL_ENCODERS_PATH = "models/label_encoders.pkl"
SBERT_MODEL_NAME = 'all-MiniLM-L6-v2'

class ERCDataset(Dataset):
    def __init__(self, csv_path, sbert_model):
        df = pd.read_csv(csv_path)
        # Combine Category, Subcategory, Detail_Category into a single label string
        # We handle NaNs by replacing with empty string
        df = df.fillna('')
        df['full_label'] = df['Category'] + "|" + df['Subcategory'] + "|" + df['Detail_Category']
        
        self.texts = df['normalized_activity'].tolist()
        self.labels = df['full_label'].tolist()
        
        # Encode labels
        self.unique_labels = sorted(list(set(self.labels)))
        self.label_to_idx = {l: i for i, l in enumerate(self.unique_labels)}
        self.idx_to_label = {i: l for i, l in enumerate(self.unique_labels)}
        
        print(f"Loaded {len(self.texts)} samples with {len(self.unique_labels)} unique labels.")
        
        # Pre-calculate embeddings to speed up training
        print("Pre-calculating SBERT embeddings...")
        self.embeddings = sbert_model.encode(self.texts, convert_to_tensor=True, show_progress_bar=True)

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        return self.embeddings[idx], torch.tensor(self.label_to_idx[self.labels[idx]])

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

def train_bootstrap():
    os.makedirs("models", exist_ok=True)
    
    # Load SBERT
    print(f"Loading SBERT model: {SBERT_MODEL_NAME}")
    sbert_model = SentenceTransformer(SBERT_MODEL_NAME)
    
    # Load Dataset
    dataset = ERCDataset("outputs/cleaned_training_dataset.csv", sbert_model)
    dataloader = DataLoader(dataset, batch_size=32, shuffle=True)
    
    # Initialize Agent
    input_dim = 384 # Dimension for all-MiniLM-L6-v2
    num_classes = len(dataset.unique_labels)
    agent = ERCAgent(input_dim, num_classes).to(DEVICE)
    
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(agent.parameters(), lr=0.001)
    
    # Training Loop
    num_epochs = 50
    print(f"Starting bootstrap training for {num_epochs} epochs...")
    for epoch in range(num_epochs):
        total_loss = 0
        for batch_embeddings, batch_labels in dataloader:
            batch_embeddings, batch_labels = batch_embeddings.to(DEVICE), batch_labels.to(DEVICE)
            
            optimizer.zero_grad()
            outputs = agent(batch_embeddings)
            loss = criterion(outputs, batch_labels)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
        
        if (epoch + 1) % 10 == 0:
            print(f"Epoch [{epoch+1}/{num_epochs}], Loss: {total_loss/len(dataloader):.4f}")
            
    # Save Model and Encoders
    torch.save(agent.state_dict(), MODEL_SAVE_PATH)
    with open(LABEL_ENCODERS_PATH, 'wb') as f:
        pickle.dump({
            'label_to_idx': dataset.label_to_idx,
            'idx_to_label': dataset.idx_to_label,
            'unique_labels': dataset.unique_labels
        }, f)
        
    print(f"Bootstrap training complete. Model saved to {MODEL_SAVE_PATH}")

if __name__ == "__main__":
    train_bootstrap()
