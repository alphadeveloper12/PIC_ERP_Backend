import pandas as pd
import numpy as np
from .models import Section, Subsection, BOQItem
import hashlib
from rl_engine.rl_feedback_loop import RLFeedbackHandler, DEVICE
from rl_engine.link_boq_primavera_rl import ERC_MAP
import re
import torch


def extract_boq(file_or_df, boq):
    # Initialize classifier and generator
    handler = RLFeedbackHandler()
    try:
        # Extract data from the file or use provided DataFrame
        if isinstance(file_or_df, pd.DataFrame):
            boq_data = file_or_df
        else:
            boq_data = pd.read_excel(file_or_df)

        # If columns are numeric (no headers), try to find the header row or assign defaults
        if all(isinstance(c, int) for c in boq_data.columns):
            # Look for a row that contains 'Description'
            for idx, row in boq_data.iterrows():
                if any('Description' in str(val) for val in row):
                    boq_data.columns = boq_data.iloc[idx]
                    boq_data = boq_data.iloc[idx + 1:].reset_index(drop=True)
                    break
            else:
                # Fallback: assume standard order if no header found
                cols = {0: 'Description', 1: 'Unit', 2: 'Quantity', 3: 'Rate', 4: 'Amount'}
                boq_data = boq_data.rename(columns=cols)

        boq_data = boq_data.dropna(subset=['Description'])

        # Create lists to hold objects for bulk creation
        sections = []
        subsections = []
        boq_items = []

        # Dictionaries to store the existing sections and subsections for quick lookup
        section_lookup = {}
        subsection_lookup = {}

        current_section = None
        current_subsection = None

        # First pass: Identify sections, subsections, and collect item descriptions
        item_data_list = []
        for index, row in boq_data.iterrows():
            description = str(row.get('Description', '')).strip()
            if not description: continue

            if 'SECTION' in description:
                if description not in section_lookup:
                    current_section = Section(name=description, boq=boq)
                    sections.append(current_section)
                    section_lookup[description] = current_section
                else:
                    current_section = section_lookup[description]
            elif len(description.split(' - ')) == 2:
                if current_section:
                    if description not in subsection_lookup:
                        current_subsection = Subsection(name=description, section=current_section)
                        subsections.append(current_subsection)
                        subsection_lookup[description] = current_subsection
                    else:
                        current_subsection = subsection_lookup[description]
            else:
                if current_subsection:
                    unit = str(row.get('Unit', '')).strip()

                    def clean_numeric(val):
                        if pd.isna(val):
                            return 0
                        if isinstance(val, (int, float)):
                            return val
                        # Remove non-numeric characters except decimal point
                        cleaned = re.sub(r'[^\d.]', '', str(val))
                        try:
                            return float(cleaned) if cleaned else 0
                        except ValueError:
                            return 0

                    quantity = clean_numeric(row.get('Quantity'))
                    rate = clean_numeric(row.get('Rate'))
                    amount = clean_numeric(row.get('Amount'))

                    item_data_list.append({
                        'description': description,
                        'unit': unit,
                        'quantity': quantity,
                        'rate': rate,
                        'amount': amount,
                        'subsection': current_subsection
                    })

        # Batch predict ERC codes
        if item_data_list:
            descriptions = [item['description'] for item in item_data_list]
            
            # Predict using RL Handler
            with torch.no_grad():
                embeddings = handler.sbert_model.encode(descriptions, convert_to_tensor=True).to(DEVICE)
                handler.agent.eval()
                outputs = handler.agent(embeddings)
                probs = torch.softmax(outputs, dim=1)
                confs, pred_indices = torch.max(probs, dim=1)
            
            predictions = [handler.idx_to_label[idx.item()] for idx in pred_indices]

            for i, item_data in enumerate(item_data_list):
                prediction_full = predictions[i]
                
                # Split label into parts (Category|Subcategory|Detail)
                parts = prediction_full.split('|')
                cats = [p for p in parts if p]
                
                # Map to EC Codes
                erc_codes_list = [ERC_MAP.get(c, '') for c in cats if c in ERC_MAP]
                erc_code = "-".join([c for c in erc_codes_list if c])

                boq_items.append(BOQItem(
                    description=item_data['description'],
                    unit=item_data['unit'],
                    quantity=item_data['quantity'],
                    rate=item_data['rate'],
                    amount=item_data['amount'],
                    subsection=item_data['subsection'],
                    ERC_code=erc_code
                ))

        # Save sections, subsections, and BOQItems to the database
        if sections:
            Section.objects.bulk_create(sections)
        if subsections:
            Subsection.objects.bulk_create(subsections)
        if boq_items:
            BOQItem.objects.bulk_create(boq_items)

        return True

    except Exception as e:
        print(f'Exception inside: BOQ extraction Function {str(e)}')
        return False


def calculate_file_hash(file):
    """
    Calculate the SHA256 hash of the file content.
    """
    hash_sha256 = hashlib.sha256()
    for chunk in file.chunks():
        hash_sha256.update(chunk)
    return hash_sha256.hexdigest()