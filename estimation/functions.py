import pandas as pd
import numpy as np
from .models import Section, Subsection, BOQItem
import hashlib
from planning.services.erc_model import ERCModel
import re


def extract_boq(file_or_df, boq):
    # Initialize ERC Model
    erc_model = ERCModel()
    erc_model.load_model()
    try:
        # Extract data from the file or use provided DataFrame
        if isinstance(file_or_df, pd.DataFrame):
            boq_data = file_or_df
        else:
            boq_data = pd.read_excel(file_or_df)

        # If columns are numeric (no headers), try to find the header row or assign defaults
        if all(isinstance(c, int) for c in boq_data.columns):
            # Look for a row that contains 'description' or 'Description'
            for idx, row in boq_data.iterrows():
                if any(str(val).lower() == 'description' for val in row):
                    boq_data.columns = [str(c).lower().strip() for c in boq_data.iloc[idx]]
                    boq_data = boq_data.iloc[idx + 1:].reset_index(drop=True)
                    break
            else:
                # Fallback: assume standard order if no header found
                cols = {0: 'description', 1: 'unit', 2: 'quantity', 3: 'rate', 4: 'amount'}
                boq_data = boq_data.rename(columns=cols)

        # Standardize columns again just in case (e.g. if header detection found Title Case)
        boq_data.columns = [str(col).strip().lower() for col in boq_data.columns]

        if 'description' not in boq_data.columns:
             print("Error: 'description' column not found in BOQ data.")
             return False

        boq_data = boq_data.dropna(subset=['description'])

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
            description = str(row.get('description', '')).strip()
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
                    unit = str(row.get('unit', '')).strip()

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

                    quantity = clean_numeric(row.get('quantity'))
                    rate = clean_numeric(row.get('rate'))
                    amount = clean_numeric(row.get('amount'))

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
            
            # Predict using ERC Model
            predictions = erc_model.predict(descriptions)

            for i, item_data in enumerate(item_data_list):
                erc_code = predictions[i]

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