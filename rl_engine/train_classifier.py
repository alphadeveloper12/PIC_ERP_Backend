"""
Multi-Output Text Classifier for Activity Descriptions
Using DistilBERT with separate classification heads for each target

This script:
1. Loads augmented training data
2. Trains a DistilBERT-based multi-output classifier
3. Evaluates performance on each target column
4. Saves trained model and label encoders
"""

import os
import json
import pickle
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torch.optim import AdamW
from transformers import (
    DistilBertTokenizer, 
    DistilBertModel,
    get_linear_schedule_with_warmup
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG = {
    'data_path': 'inputs/combined_training_data.xlsx',
    'model_save_dir': 'models/activity_classifier',
    'model_name': 'distilbert-base-uncased',
    'max_length': 128,
    'batch_size': 16,
    'epochs': 10,
    'learning_rate': 2e-5,
    'warmup_ratio': 0.1,
    'hidden_dim': 256,
    'dropout': 0.3,
    'test_size': 0.2,
    'random_state': 42,
    'device': 'cuda' if torch.cuda.is_available() else 'cpu'
}

TARGET_COLUMNS = ['Level1_Desc', 'Level2_Desc', 'Level3_Desc', 'Family_Desc', 'Main_Desc']

# ============================================================================
# DATASET CLASS
# ============================================================================

class ActivityDataset(Dataset):
    """Custom Dataset for Activity Classification."""
    
    def __init__(self, texts, labels_dict, tokenizer, max_length):
        self.texts = texts
        self.labels_dict = labels_dict  # Dict of {target_col: encoded_labels}
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = str(self.texts[idx])
        
        encoding = self.tokenizer(
            text,
            add_special_tokens=True,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        item = {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
        }
        
        # Add labels for each target column
        for col, labels in self.labels_dict.items():
            item[f'{col}_label'] = torch.tensor(labels[idx], dtype=torch.long)
            # Mask for handling missing values (-1)
            item[f'{col}_mask'] = torch.tensor(1 if labels[idx] != -1 else 0, dtype=torch.float)
        
        return item


# ============================================================================
# MODEL ARCHITECTURE
# ============================================================================

class MultiOutputClassifier(nn.Module):
    """DistilBERT-based multi-output classifier with separate heads."""
    
    def __init__(self, model_name, num_classes_dict, hidden_dim=256, dropout=0.3):
        super().__init__()
        
        # Load pre-trained DistilBERT
        self.bert = DistilBertModel.from_pretrained(model_name)
        bert_hidden = self.bert.config.hidden_size  # 768 for distilbert-base
        
        # Shared dense layer
        self.shared = nn.Sequential(
            nn.Linear(bert_hidden, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout)
        )
        
        # Separate classification heads for each target
        self.classifiers = nn.ModuleDict({
            col: nn.Linear(hidden_dim, num_classes)
            for col, num_classes in num_classes_dict.items()
        })
    
    def forward(self, input_ids, attention_mask):
        # Get BERT embeddings
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        
        # Use [CLS] token representation
        pooled_output = outputs.last_hidden_state[:, 0, :]
        
        # Shared representation
        shared_repr = self.shared(pooled_output)
        
        # Get logits from each classification head
        logits = {
            col: classifier(shared_repr)
            for col, classifier in self.classifiers.items()
        }
        
        return logits


# ============================================================================
# TRAINING FUNCTIONS
# ============================================================================

def compute_loss(logits, batch, target_columns):
    """Compute masked cross-entropy loss for all targets."""
    total_loss = 0.0
    loss_fn = nn.CrossEntropyLoss(reduction='none')
    
    for col in target_columns:
        labels = batch[f'{col}_label']
        mask = batch[f'{col}_mask']
        
        # Compute loss only for non-missing labels
        col_logits = logits[col]
        
        # Replace -1 labels with 0 temporarily (they'll be masked anyway)
        safe_labels = torch.where(labels == -1, torch.zeros_like(labels), labels)
        
        loss = loss_fn(col_logits, safe_labels)
        masked_loss = (loss * mask).sum() / (mask.sum() + 1e-8)
        
        total_loss += masked_loss
    
    return total_loss / len(target_columns)


def train_epoch(model, dataloader, optimizer, scheduler, device, target_columns):
    """Train for one epoch."""
    model.train()
    total_loss = 0
    
    progress_bar = tqdm(dataloader, desc="Training", leave=False)
    
    for batch in progress_bar:
        # Move to device
        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        batch = {k: v.to(device) for k, v in batch.items()}
        
        # Forward pass
        optimizer.zero_grad()
        logits = model(input_ids, attention_mask)
        
        # Compute loss
        loss = compute_loss(logits, batch, target_columns)
        
        # Backward pass
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        scheduler.step()
        
        total_loss += loss.item()
        progress_bar.set_postfix({'loss': f'{loss.item():.4f}'})
    
    return total_loss / len(dataloader)


def evaluate(model, dataloader, device, target_columns, label_encoders):
    """Evaluate model and return metrics."""
    model.eval()
    
    all_predictions = {col: [] for col in target_columns}
    all_labels = {col: [] for col in target_columns}
    all_masks = {col: [] for col in target_columns}
    
    with torch.no_grad():
        for batch in tqdm(dataloader, desc="Evaluating", leave=False):
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            
            logits = model(input_ids, attention_mask)
            
            for col in target_columns:
                preds = torch.argmax(logits[col], dim=1).cpu().numpy()
                labels = batch[f'{col}_label'].cpu().numpy()
                masks = batch[f'{col}_mask'].cpu().numpy()
                
                all_predictions[col].extend(preds)
                all_labels[col].extend(labels)
                all_masks[col].extend(masks)
    
    # Calculate metrics for each target
    results = {}
    
    print("\n" + "="*70)
    print(" EVALUATION RESULTS")
    print("="*70)
    
    for col in target_columns:
        preds = np.array(all_predictions[col])
        labels = np.array(all_labels[col])
        masks = np.array(all_masks[col])
        
        # Filter out masked samples
        valid_idx = masks == 1
        if valid_idx.sum() == 0:
            print(f"\n{col}: No valid samples to evaluate")
            continue
            
        valid_preds = preds[valid_idx]
        valid_labels = labels[valid_idx]
        
        accuracy = accuracy_score(valid_labels, valid_preds)
        
        print(f"\n--- {col} ---")
        print(f"Accuracy: {accuracy:.4f} ({valid_idx.sum()} samples)")
        
        # Decode labels for detailed report
        le = label_encoders[col]
        try:
            decoded_preds = le.inverse_transform(valid_preds)
            decoded_labels = le.inverse_transform(valid_labels)
            print(classification_report(decoded_labels, decoded_preds, 
                                         zero_division=0, 
                                         labels=le.classes_[:min(10, len(le.classes_))]))
        except Exception as e:
            print(f"Could not generate detailed report: {e}")
        
        results[col] = {
            'accuracy': accuracy,
            'num_samples': int(valid_idx.sum())
        }
    
    return results


# ============================================================================
# DATA PREPARATION
# ============================================================================

def prepare_data(config):
    """Load and prepare data for training."""
    print("Loading data...")
    df = pd.read_excel(config['data_path'])
    
    # Filter rows that have at least one non-null target
    mask = df[TARGET_COLUMNS].notna().any(axis=1)
    df = df[mask].reset_index(drop=True)
    
    print(f"Total samples with at least one label: {len(df)}")
    
    # Prepare label encoders
    label_encoders = {}
    encoded_labels = {}
    num_classes = {}
    
    for col in TARGET_COLUMNS:
        le = LabelEncoder()
        
        # Get all non-null values
        non_null_values = df[col].dropna().unique()
        le.fit(non_null_values)
        
        # Encode labels (-1 for missing values)
        labels = []
        for val in df[col]:
            if pd.isna(val):
                labels.append(-1)
            else:
                labels.append(le.transform([val])[0])
        
        label_encoders[col] = le
        encoded_labels[col] = np.array(labels)
        num_classes[col] = len(le.classes_)
        
        print(f"  {col}: {num_classes[col]} classes")
    
    # Split data
    texts = df['Activity_Description'].values
    
    train_idx, val_idx = train_test_split(
        np.arange(len(texts)),
        test_size=config['test_size'],
        random_state=config['random_state']
    )
    
    train_texts = texts[train_idx]
    val_texts = texts[val_idx]
    
    train_labels = {col: encoded_labels[col][train_idx] for col in TARGET_COLUMNS}
    val_labels = {col: encoded_labels[col][val_idx] for col in TARGET_COLUMNS}
    
    print(f"\nTrain samples: {len(train_texts)}")
    print(f"Validation samples: {len(val_texts)}")
    
    return train_texts, val_texts, train_labels, val_labels, label_encoders, num_classes


# ============================================================================
# MAIN TRAINING LOOP
# ============================================================================

def train_model(config):
    """Main training function."""
    print("\n" + "="*70)
    print(" TRAINING MULTI-OUTPUT ACTIVITY CLASSIFIER")
    print("="*70)
    print(f"Device: {config['device']}")
    print(f"Model: {config['model_name']}")
    
    # Prepare data
    train_texts, val_texts, train_labels, val_labels, label_encoders, num_classes = prepare_data(config)
    
    # Load tokenizer
    print("\nLoading tokenizer...")
    tokenizer = DistilBertTokenizer.from_pretrained(config['model_name'])
    
    # Create datasets
    train_dataset = ActivityDataset(train_texts, train_labels, tokenizer, config['max_length'])
    val_dataset = ActivityDataset(val_texts, val_labels, tokenizer, config['max_length'])
    
    train_loader = DataLoader(train_dataset, batch_size=config['batch_size'], shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=config['batch_size'], shuffle=False)
    
    # Initialize model
    print("\nInitializing model...")
    model = MultiOutputClassifier(
        config['model_name'],
        num_classes,
        hidden_dim=config['hidden_dim'],
        dropout=config['dropout']
    )
    model.to(config['device'])
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Total parameters: {total_params:,}")
    print(f"Trainable parameters: {trainable_params:,}")
    
    # Optimizer and scheduler
    optimizer = AdamW(model.parameters(), lr=config['learning_rate'])
    total_steps = len(train_loader) * config['epochs']
    warmup_steps = int(total_steps * config['warmup_ratio'])
    scheduler = get_linear_schedule_with_warmup(
        optimizer, 
        num_warmup_steps=warmup_steps,
        num_training_steps=total_steps
    )
    
    # Training loop
    best_val_acc = 0
    history = {'train_loss': [], 'val_results': []}
    
    print("\n" + "-"*70)
    print(" STARTING TRAINING")
    print("-"*70)
    
    for epoch in range(config['epochs']):
        print(f"\nEpoch {epoch + 1}/{config['epochs']}")
        
        # Train
        train_loss = train_epoch(model, train_loader, optimizer, scheduler, 
                                  config['device'], TARGET_COLUMNS)
        history['train_loss'].append(train_loss)
        print(f"Train Loss: {train_loss:.4f}")
        
        # Evaluate
        val_results = evaluate(model, val_loader, config['device'], 
                               TARGET_COLUMNS, label_encoders)
        history['val_results'].append(val_results)
        
        # Calculate average accuracy
        accuracies = [r['accuracy'] for r in val_results.values() if 'accuracy' in r]
        if accuracies:
            avg_acc = np.mean(accuracies)
            print(f"\nAverage Validation Accuracy: {avg_acc:.4f}")
            
            # Save best model
            if avg_acc > best_val_acc:
                best_val_acc = avg_acc
                save_model(model, tokenizer, label_encoders, config, history)
                print("✓ Best model saved!")
    
    print("\n" + "="*70)
    print(f" TRAINING COMPLETE - Best Avg Accuracy: {best_val_acc:.4f}")
    print("="*70)
    
    return model, tokenizer, label_encoders, history


def save_model(model, tokenizer, label_encoders, config, history):
    """Save model, tokenizer, and label encoders."""
    save_dir = config['model_save_dir']
    os.makedirs(save_dir, exist_ok=True)
    
    # Save model state
    torch.save(model.state_dict(), os.path.join(save_dir, 'model.pt'))
    
    # Save tokenizer
    tokenizer.save_pretrained(os.path.join(save_dir, 'tokenizer'))
    
    # Save label encoders
    with open(os.path.join(save_dir, 'label_encoders.pkl'), 'wb') as f:
        pickle.dump(label_encoders, f)
    
    # Save config and metadata
    metadata = {
        'config': config,
        'num_classes': {col: len(le.classes_) for col, le in label_encoders.items()},
        'class_names': {col: list(le.classes_) for col, le in label_encoders.items()},
        'target_columns': TARGET_COLUMNS
    }
    
    with open(os.path.join(save_dir, 'metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Save training history
    history_save = {
        'train_loss': history['train_loss'],
        'val_results': [
            {col: {'accuracy': v.get('accuracy', 0), 'num_samples': v.get('num_samples', 0)} 
             for col, v in epoch_results.items()}
            for epoch_results in history['val_results']
        ]
    }
    
    with open(os.path.join(save_dir, 'history.json'), 'w') as f:
        json.dump(history_save, f, indent=2)
    
    print(f"Model saved to {save_dir}/")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    model, tokenizer, label_encoders, history = train_model(CONFIG)
