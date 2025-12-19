import pandas as pd
import numpy as np
import re
import json
import os
from sentence_transformers import SentenceTransformer, util
import torch
from django.conf import settings
from .predict import ActivityClassifier
from collections import defaultdict

class ERCCodeGenerator:
    """Generate ERC codes from classification labels."""

    def __init__(self):
        # Hardcoded mappings based on model labels
        self.level1_map = {
            'Closeout': 'CL',
            'Construction': 'CN',
            'General': 'GN',
            'Method Statements': 'MS',
            'Shop Drawing': 'SD'
        }
        self.level2_map = {
            'Architectural': 'AR',
            'Authority Drawings': 'AD',
            'Building Permits': 'BP',
            'Controlled Milestones': 'CM',
            'Documentation': 'DC',
            'Key Milestone': 'KM',
            'MEP related items': 'MP',
            'Mobilization': 'MB',
            'No Objection Certificates (Authority approvals)': 'NO',
            'Structure': 'ST',
            'Submission': 'SB'
        }
        self.level3_map = {
            'Consultant Approval': 'CA',
            'Submission': 'SB',
            'Work Execution': 'WE'
        }
        self.family_map = {
            'Electrical Power & Lighting': 'EL',
            'External Finishes': 'EF',
            'External Works': 'EW',
            'Gas / LPG System': 'GS',
            'HVAC Systems Family': 'HV',
            'Internal Finishes': 'IF',
            'MEP General': 'MG',
            'Plumbing & Drainage Family': 'PD',
            'Structural Works': 'SW'
        }
        self.main_map = {
            'Balcony & Balustrade Works': 'BB',
            'Boundary Walls & Fencing': 'BW',
            'Builders Work for MEP': 'BM',
            'Doors & Windows': 'DW',
            'Drainage Works': 'DR',
            'Electrical Power Works': 'EP',
            'Elevation / Façade Works': 'EV',
            'Floor & Wall Tiling Works': 'FT',
            'Gypsum / Ceiling Works': 'GC',
            'Kitchen Units & Counters': 'KC',
            'LPG / Gas Works': 'LG',
            'Lighting Works': 'LW',
            'Not Applicable': 'NA',
            'Painting Works': 'PW',
            'Plaster Works': 'PL',
            'Sanitary Fixtures & Accessories': 'SF',
            'Screed Works': 'SC',
            'Tiling Works': 'TL',
            'Wall Tiling Works': 'WT',
            'Wardrobes & Closets': 'WC',
            'Waterproofing Works': 'WP'
        }

    def generate_code(self, level1, level2, level3=None, family=None, main=None, seq="000"):
        parts = []
        parts.append(self.level1_map.get(level1, 'UN'))
        parts.append(self.level2_map.get(level2, 'UN'))
        if level3: parts.append(self.level3_map.get(level3, 'UN'))
        if family: parts.append(self.family_map.get(family, 'UN'))
        if main: parts.append(self.main_map.get(main, 'UN'))
        parts.append(seq)
        return "-".join(parts)

    def get_prefix(self, erc_code):
        """Extract the non-numeric part of the ERC code."""
        if not erc_code:
            return ""
        parts = erc_code.split('-')
        # Assuming the last part is the numeric sequence
        return "-".join(parts[:-1])


def clean_boq_data_util(input_file_path):
    """
    Cleans the BOQ data from a file path and returns a cleaned DataFrame.
    """
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
    """
    Cleans Primavera P6 data from a file path and returns a cleaned DataFrame.
    """
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


def link_boq_to_primavera_util(serialized_boq_data, primavera_df):
    """
    Links serialized BOQ data to a Primavera DataFrame using ERC codes as a bridge.
    """
    # Initialize classifier and generator
    classifier = ActivityClassifier()
    erc_gen = ERCCodeGenerator()

    # Flatten BOQ items
    flat_items = []
    for section in serialized_boq_data.get('sections', []):
        for sub in section.get('subsections', []):
            for item in sub.get('items', []):
                item['erc_prefix'] = erc_gen.get_prefix(item.get('ERC_code'))
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

    # Predict ERC codes for Primavera activities
    prim_activities = [str(r[activity_col]) for r in prim_data]
    predictions = classifier.predict_batch(prim_activities)

    # Group Primavera activities by ERC prefix for O(1) lookup
    prim_by_prefix = defaultdict(list)
    for i, record in enumerate(prim_data):
        pred = predictions[i]
        erc_code = erc_gen.generate_code(
            level1=pred.get('Level1_Desc'),
            level2=pred.get('Level2_Desc'),
            level3=pred.get('Level3_Desc'),
            family=pred.get('Family_Desc'),
            main=pred.get('Main_Desc'),
            seq=f"{i + 1:03d}"
        )
        record['ERC_code'] = erc_code
        prefix = erc_gen.get_prefix(erc_code)
        record['erc_prefix'] = prefix

        activity_match = {
            "desc": record.get(activity_col, ""),
            "ERC_code": erc_code,
            "Original Duration": record.get("Original Duration", 0),
            "Early Start": record.get("Early Start", 0),
            "Early Finish": record.get("Early Finish", 0),
            "Late Start": record.get("Late Start", 0),
            "Late Finish": record.get("Late Finish", 0),
            "Total Float": record.get("Total Float", 0),
            "Budgeted Total Cost": record.get("Budgeted Total Cost", 0),
            "Score": 1.0  # Exact ERC prefix match
        }
        prim_by_prefix[prefix].append(activity_match)

    # Link by ERC prefix using dictionary lookup
    for item in flat_items:
        boq_prefix = item.get('erc_prefix')
        if boq_prefix in prim_by_prefix:
            item["primavera_activities"].extend(prim_by_prefix[boq_prefix])

    # Cleanup temporary fields
    for item in flat_items:
        if 'erc_prefix' in item:
            del item['erc_prefix']

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
