"""
Inference Script for Activity Classification

This script:
1. Loads trained model and label encoders
2. Accepts activity descriptions as input
3. Returns predictions for all 5 target columns with confidence scores
"""

import os
import json
import pickle
import torch
import torch.nn as nn
from transformers import DistilBertTokenizer, DistilBertModel
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

MODEL_DIR = 'models/activity_classifier'

# ============================================================================
# MODEL ARCHITECTURE (must match training)
# ============================================================================

class MultiOutputClassifier(nn.Module):
    """DistilBERT-based multi-output classifier with separate heads."""
    
    def __init__(self, model_name, num_classes_dict, hidden_dim=256, dropout=0.3):
        super().__init__()
        
        self.bert = DistilBertModel.from_pretrained(model_name)
        bert_hidden = self.bert.config.hidden_size
        
        self.shared = nn.Sequential(
            nn.Linear(bert_hidden, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout)
        )
        
        self.classifiers = nn.ModuleDict({
            col: nn.Linear(hidden_dim, num_classes)
            for col, num_classes in num_classes_dict.items()
        })
    
    def forward(self, input_ids, attention_mask):
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = outputs.last_hidden_state[:, 0, :]
        shared_repr = self.shared(pooled_output)
        
        logits = {
            col: classifier(shared_repr)
            for col, classifier in self.classifiers.items()
        }
        
        return logits


# ============================================================================
# PREDICTOR CLASS
# ============================================================================

class ActivityClassifier:
    """Wrapper class for easy prediction."""
    
    _instance = None

    @classmethod
    def get_instance(cls, model_dir=MODEL_DIR):
        if cls._instance is None:
            cls._instance = cls(model_dir)
        return cls._instance

    def __init__(self, model_dir=MODEL_DIR):
        self.model_dir = model_dir
        self.device = 'cpu' # Force CPU to avoid CUDA errors in this environment
        
        # Load metadata
        with open(os.path.join(model_dir, 'metadata.json'), 'r') as f:
            self.metadata = json.load(f)
        
        # Load label encoders
        with open(os.path.join(model_dir, 'label_encoders.pkl'), 'rb') as f:
            self.label_encoders = pickle.load(f)
        
        # Load tokenizer
        self.tokenizer = DistilBertTokenizer.from_pretrained(
            os.path.join(model_dir, 'tokenizer')
        )
        
        # Load model
        config = self.metadata['config']
        self.model = MultiOutputClassifier(
            config['model_name'],
            self.metadata['num_classes'],
            hidden_dim=config['hidden_dim'],
            dropout=config['dropout']
        )
        
        state_dict = torch.load(
            os.path.join(model_dir, 'model.pt'),
            map_location=self.device
        )
        self.model.load_state_dict(state_dict)
        self.model.to(self.device)
        self.model.eval()
        
        self.target_columns = self.metadata['target_columns']
        self.max_length = config['max_length']
        
        print(f"Model loaded from {model_dir}")
        print(f"Device: {self.device}")
        print(f"Target columns: {self.target_columns}")
    
    def predict(self, texts, return_confidence=True):
        """
        Predict classifications for given texts efficiently.
        """
        if isinstance(texts, str):
            texts = [texts]
        
        if not texts:
            return []

        # Tokenize
        encodings = self.tokenizer(
            texts,
            add_special_tokens=True,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        input_ids = encodings['input_ids'].to(self.device)
        attention_mask = encodings['attention_mask'].to(self.device)
        
        # Predict
        with torch.no_grad():
            logits_dict = self.model(input_ids, attention_mask)
        
        # Process results using batch operations
        predictions_by_col = {}
        confidences_by_col = {}
        
        for col in self.target_columns:
            logits = logits_dict[col]
            probs = torch.softmax(logits, dim=1)
            
            confidences, indices = torch.max(probs, dim=1)
            
            # Batch inverse transform
            le = self.label_encoders[col]
            pred_labels = le.inverse_transform(indices.cpu().numpy())
            
            predictions_by_col[col] = pred_labels
            confidences_by_col[col] = confidences.cpu().numpy()
        
        # Assemble final results
        results = []
        for i in range(len(texts)):
            result = {'Activity_Description': texts[i]}
            for col in self.target_columns:
                result[col] = predictions_by_col[col][i]
                if return_confidence:
                    result[f'{col}_confidence'] = round(float(confidences_by_col[col][i]), 4)
            results.append(result)
        
        return results
    
    def get_embeddings(self, texts):
        """
        Get BERT embeddings for a list of texts.
        """
        if isinstance(texts, str):
            texts = [texts]
        
        if not texts:
            return []

        # Tokenize
        encodings = self.tokenizer(
            texts,
            add_special_tokens=True,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        input_ids = encodings['input_ids'].to(self.device)
        attention_mask = encodings['attention_mask'].to(self.device)
        
        # Get embeddings
        with torch.no_grad():
            outputs = self.model.bert(input_ids=input_ids, attention_mask=attention_mask)
            # Use CLS token embedding (first token)
            embeddings = outputs.last_hidden_state[:, 0, :]
            
        return embeddings.cpu().numpy()
    
    def predict_with_top_k(self, text, k=3):
        """
        Predict with top-k alternatives for each column.
        
        Args:
            text: Single text to classify
            k: Number of top predictions to return
            
        Returns:
            Dictionary with top-k predictions per column
        """
        # Tokenize
        encoding = self.tokenizer(
            text,
            add_special_tokens=True,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        input_ids = encoding['input_ids'].to(self.device)
        attention_mask = encoding['attention_mask'].to(self.device)
        
        # Predict
        with torch.no_grad():
            logits = self.model(input_ids, attention_mask)
        
        result = {'Activity_Description': text, 'predictions': {}}
        
        for col in self.target_columns:
            col_logits = logits[col][0]
            probs = torch.softmax(col_logits, dim=0)
            
            top_k_values, top_k_indices = torch.topk(probs, min(k, len(probs)))
            
            le = self.label_encoders[col]
            top_k_preds = []
            
            for idx, conf in zip(top_k_indices.tolist(), top_k_values.tolist()):
                label = le.inverse_transform([idx])[0]
                top_k_preds.append({'label': label, 'confidence': round(conf, 4)})
            
            result['predictions'][col] = top_k_preds
        
        return result
    
    def predict_batch(self, texts, batch_size=32):
        """
        Predict for a large batch of texts efficiently.
        
        Args:
            texts: List of texts
            batch_size: Batch size for processing
            
        Returns:
            List of prediction dictionaries
        """
        all_results = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            results = self.predict(batch, return_confidence=True)
            all_results.extend(results)
        
        return all_results
    
    def predict_dataframe(self, df, text_column='Activity_Description'):
        """
        Add predictions to a dataframe.
        
        Args:
            df: Input dataframe with activity descriptions
            text_column: Name of the text column
            
        Returns:
            Dataframe with prediction columns added
        """
        texts = df[text_column].tolist()
        predictions = self.predict_batch(texts)
        
        pred_df = pd.DataFrame(predictions)
        
        # Rename prediction columns to avoid conflicts
        rename_cols = {col: f'Predicted_{col}' for col in self.target_columns}
        rename_cols.update({f'{col}_confidence': f'Predicted_{col}_confidence' 
                           for col in self.target_columns})
        pred_df = pred_df.rename(columns=rename_cols)
        
        # Drop the duplicate text column
        pred_df = pred_df.drop(columns=['Activity_Description'])
        
        # Concatenate
        result_df = pd.concat([df.reset_index(drop=True), pred_df], axis=1)
        
        return result_df


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

def main():
    print("="*70)
    print(" ACTIVITY CLASSIFIER - INFERENCE DEMO")
    print("="*70)
    
    # Load classifier
    classifier = ActivityClassifier(MODEL_DIR)
    
    # Example predictions
    test_activities = [
        "Prepare & Submit of SD for Ground Floor Flooring Tile",
        "Review & Approval of Kitchen Cabinet Installation",
        "Completion of DEWA Electrical Power On",
        "Maintenance of Site Facilities/Preliminaries",
        "Installation of HVAC ducting for first floor",
        "Waterproofing works for roof level",
        "Prepare & Submit of SD for External Facade Panels"
    ]
    
    print("\n" + "-"*70)
    print(" SAMPLE PREDICTIONS")
    print("-"*70)
    
    for activity in test_activities:
        print(f"\n📝 Activity: {activity}")
        
        result = classifier.predict_with_top_k(activity, k=2)
        
        for col in classifier.target_columns:
            preds = result['predictions'][col]
            primary = preds[0]
            print(f"   {col}: {primary['label']} ({primary['confidence']:.1%})")
    
    # Batch prediction example
    print("\n" + "-"*70)
    print(" BATCH PREDICTION")
    print("-"*70)
    
    batch_results = classifier.predict(test_activities[:3], return_confidence=True)
    
    for result in batch_results:
        print(f"\n{result['Activity_Description'][:50]}...")
        for col in classifier.target_columns:
            print(f"  → {col}: {result[col]}")


if __name__ == "__main__":
    main()
