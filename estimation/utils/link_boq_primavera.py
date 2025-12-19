"""
BOQ and Primavera P6 Linking Script using ERC Codes

This script:
1. Cleans BOQ and Primavera data using existing functions
2. Predicts classification labels and generates ERC codes
3. Links items by matching ERC codes and semantic similarity
4. Outputs linked dataset
"""

import os
import sys
import re
import pandas as pd
import numpy as np
from tqdm import tqdm
import warnings

warnings.filterwarnings('ignore')

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from predict import ActivityClassifier


# ============================================================================
# DATA CLEANING FUNCTIONS (from data_processing.py without Django)
# ============================================================================

def clean_boq_data_util(input_file_path):
    """Cleans the BOQ data from a file path and returns a cleaned DataFrame."""
    df = pd.read_excel(input_file_path, header=None)

    # Replace empty strings and whitespace with NaN
    df = df.replace(r'^\s*$', np.nan, regex=True)

    # Remove rows that are completely empty or all NaN
    df_cleaned = df.dropna(how='all')

    # Define garbage patterns
    garbage_patterns = [
        "Carried to Collection",
        "COLLECTION",
        "Total Brought Forward from Page No.",
        "Carried to Final Summary"
    ]

    # Filter out rows containing garbage patterns
    mask = df_cleaned.apply(lambda x: x.astype(str).str.contains('|'.join(garbage_patterns), case=False, na=False)).any(
        axis=1)
    df_cleaned = df_cleaned[~mask]

    return df_cleaned


def clean_primavera_data_util(input_file_path):
    """Cleans Primavera P6 data from a file path and returns a cleaned DataFrame."""
    df = pd.read_excel(input_file_path, header=0)

    # Identify Activity Name column
    activity_col = None
    for col in df.columns:
        if 'Activity Name' in str(col):
            activity_col = col
            break

    if not activity_col:
        if len(df.columns) > 1:
            activity_col = df.columns[1]
        else:
            return df

    # Remove rows where Activity Name is NaN or empty
    df_cleaned = df.dropna(subset=[activity_col])
    df_cleaned = df_cleaned[df_cleaned[activity_col].astype(str).str.strip() != '']

    def normalize_activity(text):
        if not isinstance(text, str):
            return str(text)
        if '-Block' in text:
            text = text.split('-Block')[0]
        if ' -GH-' in text:
            text = text.split(' -GH-')[0]
        text = re.split(r'-\d+BR', text)[0]
        text = re.sub(r'\d+', '#', text)
        return text.strip()

    df_cleaned['normalized_activity'] = df_cleaned[activity_col].apply(normalize_activity)
    df_deduped = df_cleaned.drop_duplicates(subset=['normalized_activity'], keep='first')
    df_deduped = df_deduped.drop(columns=['normalized_activity'])

    return df_deduped


CONFIG = {
    'boq_path': 'inputs/boq.xlsx',
    'primavera_path': 'inputs/primavera-p6.xlsx',
    'training_data_path': 'inputs/Alana_Activities_ERC_Expanded.xlsx',
    'model_dir': 'models/activity_classifier',
    'output_path': 'outputs/linked_boq_primavera.xlsx',
}


# ============================================================================
# ERC CODE GENERATOR
# ============================================================================

class ERCCodeGenerator:
    """Generate ERC codes from classification labels using training data mappings."""

    def __init__(self, training_data_path):
        """Load training data to extract code mappings."""
        self.df = pd.read_excel(training_data_path)

        # Build description-to-code mappings
        self.level1_map = self._build_mapping('Level1_Desc', 'Level1_Code')
        self.level2_map = self._build_mapping('Level2_Desc', 'Level2_Code')
        self.level3_map = self._build_mapping('Level3_Desc', 'Level3_Code')
        self.family_map = self._build_mapping('Family_Desc', 'Family_Code')
        self.main_map = self._build_mapping('Main_Desc', 'Main_Code')

        # Add explicit mappings for new classes if not in training data
        if 'Construction' not in self.level1_map: self.level1_map['Construction'] = 'CN'
        if 'Work Execution' not in self.level3_map: self.level3_map['Work Execution'] = 'WE'
        if 'Not Applicable' not in self.main_map: self.main_map['Not Applicable'] = 'NA'

        print(f"ERC Code Generator initialized with {len(self.df)} training samples")
        print(f"  Level1 mappings: {len(self.level1_map)}")
        print(f"  Level2 mappings: {len(self.level2_map)}")
        print(f"  Level3 mappings: {len(self.level3_map)}")
        print(f"  Family mappings: {len(self.family_map)}")
        print(f"  Main mappings: {len(self.main_map)}")

    def _build_mapping(self, desc_col, code_col):
        """Build description-to-code mapping from training data."""
        mapping = {}
        for _, row in self.df.iterrows():
            desc = row[desc_col]
            code = row[code_col]
            if pd.notna(desc) and pd.notna(code):
                mapping[desc] = code
        return mapping

    def generate_code(self, level1_desc, level2_desc, level3_desc=None,
                      family_desc=None, main_desc=None, seq_id=None):
        """
        Generate ERC code from classification labels.

        Format: {Level1}-{Level2}[-{Level3}][-{Family}][-{Main}]-{SeqID}
        """
        parts = []

        # Level 1 code (required)
        level1_code = self.level1_map.get(level1_desc, 'UNK')
        parts.append(level1_code)

        # Level 2 code (required)
        level2_code = self.level2_map.get(level2_desc, 'UNK')
        parts.append(level2_code)

        # Optional codes
        if level3_desc and level3_desc in self.level3_map:
            parts.append(self.level3_map[level3_desc])

        if family_desc and family_desc in self.family_map:
            parts.append(self.family_map[family_desc])

        if main_desc and main_desc in self.main_map:
            parts.append(self.main_map[main_desc])

        # Add sequence ID
        if seq_id is not None:
            parts.append(f"{int(seq_id):03d}")
        else:
            parts.append("000")

        return "-".join(str(p) for p in parts if p)

    def generate_prefix(self, level1_desc, level2_desc, family_desc=None, main_desc=None):
        """Generate ERC prefix (Level1-Level2-Family-Main) for matching."""
        parts = []
        parts.append(self.level1_map.get(level1_desc, 'UNK'))
        parts.append(self.level2_map.get(level2_desc, 'UNK'))
        if family_desc and family_desc in self.family_map:
            parts.append(self.family_map[family_desc])
        if main_desc and main_desc in self.main_map:
            parts.append(self.main_map[main_desc])
        return "-".join(str(p) for p in parts if p)

    def generate_from_predictions(self, predictions_df, seq_start=1):
        """Generate ERC codes for a dataframe with predictions."""
        erc_codes = []

        for idx, row in predictions_df.iterrows():
            # Get predictions (may be Predicted_* or direct column names)
            level1 = row.get('Predicted_Level1_Desc') or row.get('Level1_Desc')
            level2 = row.get('Predicted_Level2_Desc') or row.get('Level2_Desc')
            level3 = row.get('Predicted_Level3_Desc') or row.get('Level3_Desc')
            family = row.get('Predicted_Family_Desc') or row.get('Family_Desc')
            main = row.get('Predicted_Main_Desc') or row.get('Main_Desc')

            code = self.generate_code(
                level1_desc=level1,
                level2_desc=level2,
                level3_desc=level3,
                family_desc=family,
                main_desc=main,
                seq_id=seq_start + idx
            )
            erc_codes.append(code)

        return erc_codes

    def generate_prefixes_from_predictions(self, predictions_df):
        """Generate ERC prefixes for a dataframe with predictions."""
        prefixes = []
        for idx, row in predictions_df.iterrows():
            level1 = row.get('Predicted_Level1_Desc') or row.get('Level1_Desc')
            level2 = row.get('Predicted_Level2_Desc') or row.get('Level2_Desc')
            family = row.get('Predicted_Family_Desc') or row.get('Family_Desc')
            main = row.get('Predicted_Main_Desc') or row.get('Main_Desc')

            prefix = self.generate_prefix(
                level1_desc=level1,
                level2_desc=level2,
                family_desc=family,
                main_desc=main
            )
            prefixes.append(prefix)
        return prefixes


# ============================================================================
# DATA CLEANING FUNCTIONS
# ============================================================================

def clean_boq(boq_path):
    """Clean BOQ data and extract descriptions."""
    print("\n[1] Cleaning BOQ data...")

    df = clean_boq_data_util(boq_path)

    # Find Description column
    desc_col = None
    for col in df.columns:
        if 'description' in str(col).lower():
            desc_col = col
            break

    if desc_col is None:
        # Use second column (index 1) as description
        desc_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]

    # Extract rows with valid descriptions
    df = df.dropna(subset=[desc_col])
    df = df[df[desc_col].astype(str).str.strip() != '']

    # Rename for consistency
    df = df.rename(columns={desc_col: 'Description'})

    print(f"  Cleaned BOQ rows: {len(df)}")
    print(f"  Sample descriptions:")
    for desc in df['Description'].head(5).values:
        print(f"    - {str(desc)[:60]}...")

    return df


def clean_primavera(primavera_path):
    """Clean Primavera data and extract activity names."""
    print("\n[2] Cleaning Primavera data...")

    df = clean_primavera_data_util(primavera_path)

    # Find Activity Name column
    activity_col = None
    for col in df.columns:
        if 'activity name' in str(col).lower():
            activity_col = col
            break

    if activity_col is None:
        activity_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]

    # Extract rows with valid activity names
    df = df.dropna(subset=[activity_col])
    df = df[df[activity_col].astype(str).str.strip() != '']

    # Rename for consistency
    df = df.rename(columns={activity_col: 'Activity_Description'})

    print(f"  Cleaned Primavera rows: {len(df)}")
    print(f"  Sample activities:")
    for desc in df['Activity_Description'].head(5).values:
        print(f"    - {str(desc)[:60]}...")

    return df


# ============================================================================
# PREDICTION AND LINKING
# ============================================================================

def predict_and_generate_erc(df, text_column, classifier, erc_generator):
    """Predict classifications and generate ERC codes."""
    print(f"\n  Predicting for {len(df)} items...")

    # Handle missing/empty texts
    texts = df[text_column].fillna('').astype(str).tolist()
    valid_texts = [t if t.strip() else "unknown item" for t in texts]

    # Batch predict
    predictions = classifier.predict_batch(valid_texts, batch_size=32)

    # Create predictions dataframe
    pred_df = pd.DataFrame(predictions)

    # Generate ERC codes
    erc_codes = erc_generator.generate_from_predictions(pred_df)
    pred_df['Generated_ERC_Code'] = erc_codes

    # Generate ERC prefixes for linking
    erc_prefixes = erc_generator.generate_prefixes_from_predictions(pred_df)
    pred_df['ERC_Prefix'] = erc_prefixes

    # Merge with original data
    result_df = pd.concat([df.reset_index(drop=True),
                           pred_df.drop(columns=['Activity_Description'], errors='ignore')],
                          axis=1)

    return result_df


def link_by_erc(boq_df, primavera_df, similarity_threshold=0.8):
    """Link BOQ and Primavera items by ERC prefix matching."""
    print("\n[4] Linking BOQ to Primavera by ERC prefix...")

    linked_records = []

    # Group Primavera by ERC prefix for fast lookup
    # Note: Using ERC_Prefix (Level1-Level2-Family-Main) instead of full code
    primavera_by_prefix = primavera_df.groupby('ERC_Prefix').apply(
        lambda x: x.to_dict('records')
    ).to_dict()

    unmatched_count = 0

    for idx, boq_row in tqdm(boq_df.iterrows(), total=len(boq_df), desc="Linking"):
        boq_prefix = boq_row.get('ERC_Prefix', '')

        # Find matching Primavera activities by ERC prefix
        matched_activities = primavera_by_prefix.get(boq_prefix, [])

        if matched_activities:
            # Take best match (first one for now)
            best_match = matched_activities[0]

            record = {
                'BOQ_Description': boq_row.get('Description', ''),
                'BOQ_ERC_Code': boq_row.get('Generated_ERC_Code', ''),
                'BOQ_Level1': boq_row.get('Level1_Desc', ''),
                'BOQ_Level2': boq_row.get('Level2_Desc', ''),
                'BOQ_Level3': boq_row.get('Level3_Desc', ''),
                'BOQ_Family': boq_row.get('Family_Desc', ''),
                'BOQ_Main': boq_row.get('Main_Desc', ''),
                'Primavera_Activity': best_match.get('Activity_Description', ''),
                'Primavera_ERC_Code': best_match.get('Generated_ERC_Code', ''),
                'Primavera_Level1': best_match.get('Level1_Desc', ''),
                'Primavera_Level2': best_match.get('Level2_Desc', ''),
                'Match_Type': 'ERC_Prefix',
                'Match_Confidence': 1.0
            }
        else:
            # No ERC prefix match
            record = {
                'BOQ_Description': boq_row.get('Description', ''),
                'BOQ_ERC_Code': boq_row.get('Generated_ERC_Code', ''),
                'BOQ_Level1': boq_row.get('Level1_Desc', ''),
                'BOQ_Level2': boq_row.get('Level2_Desc', ''),
                'BOQ_Level3': boq_row.get('Level3_Desc', ''),
                'BOQ_Family': boq_row.get('Family_Desc', ''),
                'BOQ_Main': boq_row.get('Main_Desc', ''),
                'Primavera_Activity': '',
                'Primavera_ERC_Code': '',
                'Primavera_Level1': '',
                'Primavera_Level2': '',
                'Match_Type': 'Unmatched',
                'Match_Confidence': 0.0
            }
            unmatched_count += 1

        linked_records.append(record)

    linked_df = pd.DataFrame(linked_records)

    print(f"  Total BOQ items: {len(boq_df)}")
    print(f"  Matched by ERC Prefix: {len(boq_df) - unmatched_count}")
    print(f"  Unmatched: {unmatched_count}")

    return linked_df


# ============================================================================
# MAIN PIPELINE
# ============================================================================

def main():
    print("=" * 70)
    print(" BOQ - PRIMAVERA P6 LINKING PIPELINE")
    print("=" * 70)

    # Initialize components
    print("\n[0] Initializing components...")
    classifier = ActivityClassifier(CONFIG['model_dir'])
    erc_generator = ERCCodeGenerator(CONFIG['training_data_path'])

    # Clean data
    boq_df = clean_boq(CONFIG['boq_path'])
    primavera_df = clean_primavera(CONFIG['primavera_path'])

    # Predict and generate ERC codes
    print("\n[3] Predicting classifications and generating ERC codes...")

    print("\n  Processing BOQ...")
    boq_with_preds = predict_and_generate_erc(boq_df, 'Description', classifier, erc_generator)

    print("\n  Processing Primavera...")
    primavera_with_preds = predict_and_generate_erc(primavera_df, 'Activity_Description', classifier, erc_generator)

    # Link datasets
    linked_df = link_by_erc(boq_with_preds, primavera_with_preds)

    # Save outputs
    print("\n[5] Saving outputs...")

    os.makedirs('outputs', exist_ok=True)

    # Save linked data
    linked_df.to_excel(CONFIG['output_path'], index=False)
    print(f"  Linked data saved to: {CONFIG['output_path']}")

    # Save individual predictions
    boq_with_preds.to_excel('outputs/boq_with_predictions.xlsx', index=False)
    print(f"  BOQ predictions saved to: outputs/boq_with_predictions.xlsx")

    primavera_with_preds.to_excel('outputs/primavera_with_predictions.xlsx', index=False)
    print(f"  Primavera predictions saved to: outputs/primavera_with_predictions.xlsx")

    print("\n" + "=" * 70)
    print(" PIPELINE COMPLETE")
    print("=" * 70)

    # Summary
    print(f"\nSummary:")
    print(f"  BOQ items processed: {len(boq_df)}")
    print(f"  Primavera activities processed: {len(primavera_df)}")
    print(f"  Linked records: {len(linked_df)}")
    print(f"  ERC Prefix matches: {len(linked_df[linked_df['Match_Type'] == 'ERC_Prefix'])}")
    print(f"  Unmatched: {len(linked_df[linked_df['Match_Type'] == 'Unmatched'])}")

    return linked_df, boq_with_preds, primavera_with_preds


if __name__ == "__main__":
    linked_df, boq_df, primavera_df = main()
