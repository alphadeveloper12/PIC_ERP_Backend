import pandas as pd
import numpy as np
from .models import Section, Subsection, BOQItem
import hashlib


def extract_boq(file, boq):
    try:
        # Extract data from the file
        boq_data = pd.read_excel(file)
        boq_data = boq_data.dropna(subset=['Description'])  # Remove rows with missing description

        current_section = None
        current_subsection = None

        # Create lists to hold objects for bulk creation
        sections = []
        subsections = []
        boq_items = []

        # Dictionaries to store the existing sections and subsections for quick lookup
        section_lookup = {}
        subsection_lookup = {}

        # Iterate through the rows and extract data
        for index, row in boq_data.iterrows():
            description = row.get('Description', '')
            # Ensure description is a string and strip any leading/trailing spaces
            description = str(description) if description is not None else ''
            description = description.strip()

            # Check if it's a section and create it
            if 'SECTION' in description:
                # Check if the section already exists in the in-memory lookup
                if description not in section_lookup:
                    # If not, create and add it to the list and lookup
                    current_section = Section(name=description, boq=boq)
                    sections.append(current_section)  # Append the section to the list
                    section_lookup[description] = current_section

            elif len(description.split(' - ')) == 2:  # Matches the pattern "B4 - SITE PREPARATION"
                # Ensure that current_section is set before creating a subsection
                if current_section:
                    # Check if the subsection already exists in the in-memory lookup
                    if description not in subsection_lookup:
                        # If not, create and add it to the list and lookup
                        current_subsection = Subsection(name=description, section=current_section)
                        subsections.append(current_subsection)  # Append the subsection to the list
                        subsection_lookup[description] = current_subsection

            else:
                if current_subsection:  # Ensure that the current subsection exists
                    # Safely handle non-string types for 'Unit'
                    unit = row.get('Unit', '')
                    unit = str(unit) if isinstance(unit, (str, float)) else ''  # Convert to string if needed
                    unit = unit.strip() if isinstance(unit, str) else ''

                    # Ensure that the numeric fields (Quantity, Rate, Amount) are valid numbers
                    quantity = row.get('Quantity', np.nan)
                    rate = row.get('Rate', np.nan)
                    amount = row.get('Amount', np.nan)

                    # Convert NaN or "nan" to 0 for numeric fields
                    if isinstance(quantity, str) and quantity.lower() == "nan":
                        quantity = 0
                    elif pd.isna(quantity):
                        quantity = 0

                    if isinstance(rate, str) and rate.lower() == "nan":
                        rate = 0
                    elif pd.isna(rate):
                        rate = 0

                    if isinstance(amount, str) and amount.lower() == "nan":
                        amount = 0
                    elif pd.isna(amount):
                        amount = 0

                    # If any of these values are not numbers, we should set them to 0
                    if not isinstance(quantity, (int, float)):
                        quantity = 0
                    if not isinstance(rate, (int, float)):
                        rate = 0
                    if not isinstance(amount, (int, float)):
                        amount = 0

                    # Create the BOQItem instance and associate it with the subsection
                    boq_items.append(BOQItem(
                        description=description,
                        unit=unit,
                        quantity=quantity,
                        rate=rate,
                        amount=amount,
                        subsection=current_subsection
                    ))

        # Save sections, subsections, and BOQItems to the database using bulk_create to reduce DB queries
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