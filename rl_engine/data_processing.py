import pandas as pd
import numpy as np
import re
import json
import os
from sentence_transformers import SentenceTransformer, util
import torch
from django.conf import settings


def read_file_robust(file_path, **kwargs):
    """
    Reads a file robustly, handling both Excel and CSV formats.
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.csv':
        return pd.read_csv(file_path, **kwargs)
    
    # Try reading as Excel first
    try:
        # Explicitly use openpyxl for .xlsx files
        if ext == '.xlsx':
            return pd.read_excel(file_path, engine='openpyxl', **kwargs)
        return pd.read_excel(file_path, **kwargs)
    except Exception as e:
        # If Excel reading fails, attempt to read as CSV as a fallback
        # This handles cases where the file might be a CSV with an .xlsx extension or no extension
        try:
            return pd.read_csv(file_path, **kwargs)
        except:
            # If both fail, raise the original Excel exception
            raise e


def clean_boq_data_util(input_file_path):
    """
    Cleans the BOQ data from a file path and returns a cleaned DataFrame.
    """
    df = read_file_robust(input_file_path, header=None)

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
    """
    Cleans Primavera P6 data from a file path and returns a cleaned DataFrame.
    """
    df = read_file_robust(input_file_path, header=0)

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


def link_boq_to_primavera_util(serialized_boq_data, primavera_df):
    """
    Links serialized BOQ data to a Primavera DataFrame and returns the hierarchical structure.
    """
    # Flatten BOQ items for matching
    flat_items = []
    for section in serialized_boq_data.get('sections', []):
        for sub in section.get('subsections', []):
            for item in sub.get('items', []):
                # Construct context for matching
                context = f"{section['name']} | {sub['name']} | {item['description']}"
                item['full_context'] = context
                item['primavera_activities'] = []
                flat_items.append(item)

    if not flat_items:
        return serialized_boq_data

    # Prepare Primavera data
    prim_data = primavera_df.to_dict('records')
    activity_col = None
    for col in primavera_df.columns:
        if 'Activity Name' in str(col):
            activity_col = col
            break
    if not activity_col:
        activity_col = primavera_df.columns[1]

    prim_activities = [str(r[activity_col]) for r in prim_data]

    # SBERT Matching
    model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
    boq_contexts = [item['full_context'] for item in flat_items]

    boq_embeddings = model.encode(boq_contexts, convert_to_tensor=True)
    prim_embeddings = model.encode(prim_activities, convert_to_tensor=True)

    cosine_scores = util.cos_sim(boq_embeddings, prim_embeddings)

    for i, item in enumerate(flat_items):
        scores = cosine_scores[i]
        top_results = torch.topk(scores, k=3)

        for score, idx in zip(top_results.values, top_results.indices):
            idx = idx.item()
            score = score.item()
            orig_record = prim_data[idx]

            activity_match = {
                "desc": orig_record.get(activity_col, ""),
                "Original Duration": orig_record.get("Original Duration", 0),
                "Early Start": orig_record.get("Early Start", 0),
                "Early Finish": orig_record.get("Early Finish", 0),
                "Late Start": orig_record.get("Late Start", 0),
                "Late Finish": orig_record.get("Late Finish", 0),
                "Total Float": orig_record.get("Total Float", 0),
                "Budgeted Total Cost": orig_record.get("Budgeted Total Cost", 0),
                "Score": round(score, 4)
            }
            item["primavera_activities"].append(activity_match)

        del item['full_context']

    return serialized_boq_data


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (pd.Timestamp, pd.DatetimeIndex)):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return str(obj)
