"""
Enhanced Data Augmentation for Better Family_Desc and Main_Desc Predictions

This script:
1. Fills missing values with expanded keyword patterns
2. Generates MORE synthetic data (100+ samples per class)
3. Creates additional training examples using templates
"""

import pandas as pd
import numpy as np
import re
from collections import defaultdict
import random

# ============================================================================
# CONFIGURATION
# ============================================================================

INPUT_FILE = "inputs/Alana_Activities_ERC_Expanded.xlsx"
OUTPUT_FILE = "inputs/augmented_training_data_v2.xlsx"

TARGET_COLUMNS = ['Level1_Desc', 'Level2_Desc', 'Level3_Desc', 'Family_Desc', 'Main_Desc']
MIN_SAMPLES_PER_CLASS = 80  # Increased minimum for better training

# ============================================================================
# EXPANDED PATTERN-BASED RULES FOR FILLING MISSING VALUES
# ============================================================================

# Keywords to Level1_Desc mapping
LEVEL1_PATTERNS = {
    'Shop Drawing': [r'shop\s*drawing', r'\bSD\b', r'prepare.*submit.*sd', r'prepare\s*&\s*submit\s*of\s*sd'],
    'Method Statements': [r'method\s*statement', r'\bMS\b', r'method.*statement', r'\bMOS\b'],
    'General': [r'mobilization', r'milestone', r'submission.*plan', r'insurance', r'bond', 
                r'commencement', r'completion', r'noc', r'preliminary', r'receipt.*ifc'],
    'Closeout': [r'closeout', r'demobiliz', r'handover', r'final\s*inspection', r'clearing.*site'],
}

# Keywords to Level2_Desc mapping  
LEVEL2_PATTERNS = {
    'Architectural': [r'architect', r'finish', r'paint', r'tile', r'ceiling', r'door', r'window', 
                      r'wardrobe', r'kitchen', r'gypsum', r'flooring', r'plaster', r'screed',
                      r'balcony', r'balustrade', r'waterproof', r'facade', r'elevation'],
    'MEP related items': [r'\bmep\b', r'electrical', r'plumbing', r'hvac', r'drainage', r'lighting',
                          r'sanitary', r'fire.*alarm', r'ac\s*system', r'ventilation', r'lpg', r'gas',
                          r'pump', r'cable', r'switch', r'socket', r'duct', r'pipe'],
    'Structure': [r'structural', r'concrete', r'slab', r'foundation', r'column', r'beam', 
                  r'reinforcement', r'rebar', r'shoring', r'formwork', r'precast', r'staircase'],
    'Mobilization': [r'mobiliz', r'site\s*facilit', r'preliminar', r'yard', r'workshop', r'fence'],
    'Key Milestone': [r'milestone', r'commencement', r'completion\s*date'],
    'Controlled Milestones': [r'controlled', r'bcc', r'dewa', r'civil\s*defence', r'hassantuk'],
    'Authority Drawings': [r'authority.*drawing', r'noc.*drawing', r'dcd.*drawing'],
    'No Objection Certificates (Authority approvals)': [r'\bnoc\b', r'no\s*objection', r'authority.*approval'],
    'Documentation': [r'document', r'clearing.*site'],
    'Submission': [r'submit', r'prepare.*submit'],
    'Building Permits': [r'permit', r'building\s*permit'],
}

# Keywords to Level3_Desc mapping
LEVEL3_PATTERNS = {
    'Submission': [r'submit', r'prepare.*submit', r'submission', r'prepare\s*&\s*submit'],
    'Consultant Approval': [r'approval', r'review.*approv', r'consultant.*review', r'review\s*&\s*approval'],
}

# EXPANDED Keywords to Family_Desc mapping
FAMILY_PATTERNS = {
    'Structural Works': [r'structural', r'concrete', r'slab', r'foundation', r'beam', r'column',
                         r'shoring', r'formwork', r'rebar', r'reinforc', r'precast.*slab', 
                         r'staircase', r'hc\s*slab'],
    'Internal Finishes': [r'internal.*finish', r'ceiling', r'gypsum', r'paint.*internal', 
                          r'floor.*tile', r'wall.*tile', r'wardrobe', r'kitchen.*unit',
                          r'kitchen.*cabinet', r'pantry', r'closet', r'rcp', r'flooring.*tile',
                          r'internal.*paint', r'emulsion', r'screed.*internal'],
    'External Finishes': [r'external.*finish', r'facade', r'elevation', r'balcon', r'balustrade',
                          r'waterproof', r'precast.*panel', r'external.*paint', r'external.*wall',
                          r'canopy', r'roof.*waterproof', r'external.*tile'],
    'External Works': [r'external.*work', r'boundary.*wall', r'fenc', r'landscap', r'paving',
                       r'interlock', r'gate', r'guardhouse', r'guard.*house', r'compound'],
    'MEP General': [r'\bmep\b', r'mep.*general', r'builder.*work.*mep', r'services.*duct'],
    'Electrical Power & Lighting': [r'electrical.*power', r'lighting', r'power.*dist', r'switch.*gear',
                                     r'cable', r'elp', r'switch', r'socket', r'db\b', r'panel.*board',
                                     r'wiring', r'conduit', r'light.*fixture', r'lamp'],
    'HVAC Systems Family': [r'hvac', r'air.*condition', r'\bac\b.*system', r'ventilation', r'duct',
                            r'fan\s*coil', r'fcu', r'ahu', r'chiller', r'refriger', r'split.*unit'],
    'Plumbing & Drainage Family': [r'plumbing', r'drainage', r'water.*supply', r'sanitary', 
                                    r'waste.*pipe', r'sewage', r'sewer', r'water.*tank',
                                    r'pump.*water', r'cistern', r'gully', r'manhole'],
    'Gas / LPG System': [r'\blpg\b', r'\bgas\b', r'gas.*system', r'gas.*pipe', r'gas.*meter',
                         r'gas.*valve', r'cooking.*gas'],
}

# EXPANDED Keywords to Main_Desc mapping
MAIN_PATTERNS = {
    'Doors & Windows': [r'door', r'window', r'aluminum.*door', r'wooden.*door', r'wood.*door',
                        r'glass.*door', r'entrance', r'glazing', r'louver', r'shutter'],
    'Waterproofing Works': [r'waterproof', r'water.*proof', r'membrane', r'bitumen', r'damp.*proof'],
    'Gypsum / Ceiling Works': [r'gypsum', r'ceiling', r'\brcp\b', r'false.*ceiling', r'drop.*ceiling',
                               r'plasterboard', r'drywall', r'access.*panel', r'ceiling.*tile'],
    'Kitchen Units & Counters': [r'kitchen', r'counter.*top', r'cabinet', r'pantry', r'worktop',
                                  r'sink.*unit', r'kitchen.*sink', r'countertop'],
    'Tiling Works': [r'tile', r'tiling', r'ceramic', r'porcelain', r'mosaic'],
    'Drainage Works': [r'drainage', r'drain', r'waste', r'sewer', r'sewage', r'gully', r'manhole'],
    'LPG / Gas Works': [r'\blpg\b', r'gas.*work', r'gas.*pipe', r'gas.*install', r'cooking.*gas'],
    'Lighting Works': [r'lighting', r'light.*fixture', r'lamp', r'luminaire', r'downlight', r'spot.*light'],
    'Boundary Walls & Fencing': [r'boundary.*wall', r'fencing', r'fence', r'compound.*wall', r'perimeter'],
    'Electrical Power Works': [r'electrical.*power', r'power.*work', r'cable.*laying', r'wiring',
                               r'conduit', r'elp', r'db\b', r'distribution.*board'],
    'Balcony & Balustrade Works': [r'balcon', r'balustrade', r'railing', r'handrail', r'guardrail'],
    'Floor & Wall Tiling Works': [r'floor.*tile', r'wall.*tile', r'flooring.*tile', r'floor.*tiling', 
                                   r'wall.*tiling'],
    'Wardrobes & Closets': [r'wardrobe', r'closet', r'built.*in.*cabinet', r'storage.*unit'],
    'Wall Tiling Works': [r'wall.*tile', r'wall.*tiling', r'backsplash'],
    'Painting Works': [r'paint', r'emulsion', r'epoxy.*paint', r'primer', r'coating', r'finish.*coat'],
    'Elevation / Façade Works': [r'facade', r'elevation', r'façade', r'cladding', r'curtain.*wall',
                                  r'external.*wall.*finish', r'acp', r'grc'],
    'Sanitary Fixtures & Accessories': [r'sanitary', r'fixture', r'wc\b', r'toilet', r'basin', r'bidet',
                                         r'shower', r'bathtub', r'faucet', r'tap', r'mirror.*cabinet'],
    'Screed Works': [r'screed', r'floor.*screed', r'cement.*screed', r'leveling'],
    'Builders Work for MEP': [r'builder.*work.*mep', r'mep.*builder', r'core.*cutting', r'sleeve',
                               r'opening.*mep', r'chasing', r'recess'],
    'Plaster Works': [r'plaster', r'render', r'internal.*plaster', r'external.*plaster'],
}

# ============================================================================
# ACTIVITY TEMPLATES FOR SYNTHETIC DATA GENERATION
# ============================================================================

ACTIVITY_TEMPLATES = {
    'Shop Drawing': [
        "Prepare & Submit of SD for {item}",
        "Shop Drawing submission for {item}",
        "Prepare SD for {item} details",
        "Submit shop drawings for {item}",
        "Develop and submit SD for {item}",
        "Create shop drawing for {item}",
        "SD preparation for {item}",
    ],
    'Method Statements': [
        "Method Statement for {item}",
        "Prepare MS for {item} installation",
        "Submit method statement for {item}",
        "Method statement preparation for {item} works",
    ],
    'Approval': [
        "Review & Approval of SD for {item}",
        "Consultant approval for {item}",
        "Review and approve SD for {item}",
        "Approval of shop drawing for {item}",
        "Review & Approval for {item} drawings",
    ],
    'Installation': [
        "Installation of {item}",
        "Install {item}",
        "{item} installation works",
        "Fixing of {item}",
        "Mounting of {item}",
    ],
    'Procurement': [
        "Procurement of {item}",
        "Material procurement for {item}",
        "Ordering of {item}",
        "Purchase of {item} materials",
    ],
}

# Items per category for template-based generation
CATEGORY_ITEMS = {
    ('Internal Finishes', 'Gypsum / Ceiling Works'): [
        'First Floor Ceiling RCP', 'Ground Floor Ceiling RCP', 'Roof Floor Ceiling',
        'Ceiling Access Panel', 'Gypsum Board Ceiling', 'False Ceiling', 'Drop Ceiling',
        'Plasterboard Partition', 'Ceiling Cornice', 'Ceiling Hatch',
    ],
    ('Internal Finishes', 'Tiling Works'): [
        'First Floor Flooring Tile', 'Ground Floor Flooring Tile', 'Bathroom Wall Tile',
        'Kitchen Backsplash Tile', 'Toilet Floor Tile', 'Living Room Floor Tile',
        'Bedroom Floor Tile', 'Ceramic Wall Tile', 'Porcelain Floor Tile',
    ],
    ('Internal Finishes', 'Floor & Wall Tiling Works'): [
        'Floor and Wall Tiles', 'Bathroom Tiling', 'Kitchen Tiling', 'Ensuite Tiling',
        'Master Bedroom Tiling', 'Guest Room Tiling', 'Common Area Tiling',
    ],
    ('Internal Finishes', 'Kitchen Units & Counters'): [
        'Kitchen Cabinet', 'Kitchen Countertop', 'Pantry Cabinet', 'Kitchen Sink Unit',
        'Kitchen Worktop', 'Kitchen Island', 'Kitchen Drawer Units', 'Kitchen Shelving',
    ],
    ('Internal Finishes', 'Wardrobes & Closets'): [
        'Master Bedroom Wardrobe', 'Guest Room Wardrobe', 'Built-in Closet', 
        'Walk-in Wardrobe', 'Storage Cabinet', 'Bedroom Cabinet', 'Dressing Room Cabinet',
    ],
    ('Internal Finishes', 'Painting Works'): [
        'Internal Paint', 'Emulsion Paint Internal', 'Ceiling Paint', 'Wall Paint',
        'Primer Coat', 'Final Paint Coat', 'Touch-up Paint', 'Interior Paint',
    ],
    ('External Finishes', 'Waterproofing Works'): [
        'Roof Waterproofing', 'Balcony Waterproofing', 'Terrace Waterproofing',
        'Canopy Waterproofing', 'Wet Area Waterproofing', 'Bathroom Waterproofing',
        'Basement Waterproofing', 'Slab Waterproofing', 'Planter Waterproofing',
    ],
    ('External Finishes', 'Balcony & Balustrade Works'): [
        'Balconies Balustrade', 'Terrace Railing', 'Staircase Handrail', 'Glass Balustrade',
        'Metal Railing', 'Balcony Guardrail', 'Roof Edge Railing',
    ],
    ('External Finishes', 'Elevation / Façade Works'): [
        'Building Elevation', 'External Facade', 'Facade Panels', 'Wall Cladding',
        'Curtain Wall', 'ACP Cladding', 'GRC Panels', 'External Wall Finish',
    ],
    ('External Works', 'Boundary Walls & Fencing'): [
        'Boundary Wall', 'Perimeter Fence', 'Compound Wall', 'Gate Posts',
        'Metal Fencing', 'Chain Link Fence', 'Precast Boundary Wall',
    ],
    ('Electrical Power & Lighting', 'Electrical Power Works'): [
        'Electrical Wiring', 'Cable Laying', 'DB Installation', 'Switch Installation',
        'Socket Installation', 'Conduit Works', 'Distribution Board', 'Main Panel',
    ],
    ('Electrical Power & Lighting', 'Lighting Works'): [
        'Light Fixtures', 'Downlight Installation', 'Ceiling Lights', 'Wall Lights',
        'Spot Lights', 'LED Lighting', 'Exterior Lighting', 'Garden Lights',
    ],
    ('Plumbing & Drainage Family', 'Drainage Works'): [
        'Drainage Pipes', 'Floor Drains', 'Drainage Manholes', 'Waste Pipes',
        'Rainwater Pipes', 'Sewage Lines', 'Gully Traps', 'Drainage Connection',
    ],
    ('Plumbing & Drainage Family', 'Sanitary Fixtures & Accessories'): [
        'WC Installation', 'Basin Installation', 'Shower Installation', 'Bathtub',
        'Bidet', 'Faucets', 'Towel Rail', 'Mirror Cabinet', 'Bathroom Accessories',
    ],
    ('Gas / LPG System', 'LPG / Gas Works'): [
        'LPG Piping', 'Gas Meter', 'Gas Valve', 'Kitchen Gas Point', 'Gas Regulator',
        'Gas Connection', 'LPG Tank', 'Gas Line Installation',
    ],
    ('HVAC Systems Family', None): [
        'FCU Installation', 'AHU Installation', 'AC Ducting', 'Ventilation Fan',
        'Split Unit Installation', 'Chiller Connection', 'AC Piping', 'Duct Insulation',
    ],
    ('Structural Works', None): [
        'Foundation Works', 'Column Concrete', 'Beam Formwork', 'Slab Reinforcement',
        'Staircase Concrete', 'Retaining Wall', 'Grade Beam', 'Pile Cap',
    ],
    ('MEP General', 'Builders Work for MEP'): [
        'Core Cutting for MEP', 'Sleeves for MEP', 'Openings for Services',
        'Chasing for Pipes', 'Recess for DB', 'MEP Coordination',
    ],
    (None, 'Doors & Windows'): [
        'Aluminum Doors', 'Wooden Doors', 'Glass Doors', 'Entrance Door', 
        'Bedroom Windows', 'Kitchen Window', 'Bathroom Window', 'Sliding Door',
        'Fire Rated Door', 'Main Entrance Door', 'Balcony Door', 'Terrace Door',
    ],
    (None, 'Screed Works'): [
        'Floor Screed', 'Cement Screed', 'Screeding Works', 'Leveling Screed',
        'Bathroom Screed', 'Kitchen Screed', 'Balcony Screed',
    ],
    (None, 'Plaster Works'): [
        'Internal Plaster', 'External Plaster', 'Wall Plaster', 'Ceiling Plaster',
        'Render Works', 'Plastering',
    ],
}

# ============================================================================
# SYNONYM REPLACEMENTS FOR TEXT AUGMENTATION
# ============================================================================

SYNONYMS = {
    'prepare': ['develop', 'draft', 'create', 'formulate', 'produce'],
    'submit': ['deliver', 'provide', 'send', 'present', 'hand over'],
    'approval': ['endorsement', 'authorization', 'sign-off', 'clearance', 'confirmation'],
    'installation': ['mounting', 'fitting', 'setup', 'placement', 'fixing'],
    'completion': ['finishing', 'finalization', 'conclusion', 'wrapping up'],
    'inspection': ['examination', 'review', 'checking', 'assessment', 'verification'],
    'work': ['activities', 'tasks', 'operations', 'jobs'],
    'construction': ['building', 'erection', 'fabrication'],
    'floor': ['level', 'storey'],
    'roof': ['rooftop', 'top level'],
    'electrical': ['electric', 'power'],
    'plumbing': ['piping', 'water system'],
    'first': ['1st', 'ground', 'lower'],
    'ground': ['first', 'lower'],
    'tile': ['tiles', 'tiling'],
    'ceiling': ['soffit', 'overhead'],
    'wall': ['partition', 'vertical surface'],
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def match_patterns(text, pattern_dict):
    """Match text against pattern dictionary and return matched category."""
    if pd.isna(text):
        return None
    text_lower = text.lower()
    for category, patterns in pattern_dict.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return category
    return None


def fill_missing_values(df):
    """Fill missing values using pattern-based rules."""
    df = df.copy()
    fill_count = defaultdict(int)
    
    for idx, row in df.iterrows():
        activity = row['Activity_Description']
        
        # Fill all target columns
        if pd.isna(row['Level1_Desc']):
            match = match_patterns(activity, LEVEL1_PATTERNS)
            if match:
                df.at[idx, 'Level1_Desc'] = match
                fill_count['Level1_Desc'] += 1
        
        if pd.isna(row['Level2_Desc']):
            match = match_patterns(activity, LEVEL2_PATTERNS)
            if match:
                df.at[idx, 'Level2_Desc'] = match
                fill_count['Level2_Desc'] += 1
        
        if pd.isna(row['Level3_Desc']):
            match = match_patterns(activity, LEVEL3_PATTERNS)
            if match:
                df.at[idx, 'Level3_Desc'] = match
                fill_count['Level3_Desc'] += 1
        
        if pd.isna(row['Family_Desc']):
            match = match_patterns(activity, FAMILY_PATTERNS)
            if match:
                df.at[idx, 'Family_Desc'] = match
                fill_count['Family_Desc'] += 1
        
        if pd.isna(row['Main_Desc']):
            match = match_patterns(activity, MAIN_PATTERNS)
            if match:
                df.at[idx, 'Main_Desc'] = match
                fill_count['Main_Desc'] += 1
    
    print("\n=== Missing Values Filled ===")
    for col, count in fill_count.items():
        print(f"  {col}: {count} values filled")
    
    return df


def augment_text(text, num_variations=5):
    """Generate text variations using synonym replacement."""
    if pd.isna(text):
        return []
    
    variations = []
    words = text.split()
    
    for _ in range(num_variations):
        new_words = []
        for word in words:
            word_lower = word.lower()
            if word_lower in SYNONYMS and random.random() > 0.4:
                synonym = random.choice(SYNONYMS[word_lower])
                if word[0].isupper():
                    synonym = synonym.capitalize()
                new_words.append(synonym)
            else:
                new_words.append(word)
        
        new_text = ' '.join(new_words)
        if new_text != text and new_text not in variations:
            variations.append(new_text)
    
    return variations


def generate_template_based_samples(df):
    """Generate synthetic samples using activity templates."""
    print("\n=== Generating Template-Based Samples ===")
    
    new_rows = []
    
    for (family, main), items in CATEGORY_ITEMS.items():
        for item in items:
            # Generate multiple activity types for each item
            for template_type, templates in ACTIVITY_TEMPLATES.items():
                template = random.choice(templates)
                activity = template.format(item=item)
                
                # Determine Level1, Level2, Level3 based on template
                if template_type == 'Shop Drawing':
                    level1 = 'Shop Drawing'
                    level3 = 'Submission'
                elif template_type == 'Method Statements':
                    level1 = 'Method Statements'
                    level3 = None
                elif template_type == 'Approval':
                    level1 = 'Shop Drawing'
                    level3 = 'Consultant Approval'
                else:
                    level1 = 'General'
                    level3 = None
                
                # Determine Level2 from family
                if family == 'Structural Works':
                    level2 = 'Structure'
                elif family in ['MEP General', 'Electrical Power & Lighting', 'HVAC Systems Family', 
                               'Plumbing & Drainage Family', 'Gas / LPG System']:
                    level2 = 'MEP related items'
                else:
                    level2 = 'Architectural'
                
                new_row = {
                    'Activity_Description': activity,
                    'Level1_Desc': level1,
                    'Level2_Desc': level2,
                    'Level3_Desc': level3,
                    'Family_Desc': family,
                    'Main_Desc': main,
                }
                new_rows.append(new_row)
    
    print(f"  Generated {len(new_rows)} template-based samples")
    return pd.DataFrame(new_rows)


def augment_underrepresented_classes(df, min_samples=MIN_SAMPLES_PER_CLASS):
    """Augment data for classes with fewer than min_samples."""
    augmented_rows = []
    
    print("\n=== Augmenting Underrepresented Classes ===")
    
    for target_col in ['Family_Desc', 'Main_Desc']:  # Focus on these
        value_counts = df[target_col].value_counts()
        
        for category, count in value_counts.items():
            if count < min_samples and pd.notna(category):
                category_rows = df[df[target_col] == category]
                samples_needed = min_samples - count
                
                print(f"  Augmenting '{category}' in {target_col}: {count} → {min_samples}")
                
                for _ in range(samples_needed):
                    source_row = category_rows.sample(1).iloc[0].copy()
                    original_text = source_row['Activity_Description']
                    
                    variations = augment_text(original_text, 5)
                    
                    if variations:
                        source_row['Activity_Description'] = random.choice(variations)
                        augmented_rows.append(source_row)
                    else:
                        # Minor variation
                        suffixes = [' (Villa)', ' (GH)', ' -Block A', ' -Type 1', ' -Phase 1']
                        source_row['Activity_Description'] = original_text + random.choice(suffixes)
                        augmented_rows.append(source_row)
    
    if augmented_rows:
        augmented_df = pd.DataFrame(augmented_rows)
        print(f"\n=== Generated {len(augmented_df)} augmented samples ===")
        return pd.concat([df, augmented_df], ignore_index=True)
    
    return df


def analyze_dataset(df, title="Dataset Analysis"):
    """Print dataset analysis."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")
    print(f"Total rows: {len(df)}")
    print(f"\nMissing values:")
    for col in TARGET_COLUMNS:
        missing = df[col].isna().sum()
        pct = (missing / len(df)) * 100
        print(f"  {col}: {missing} ({pct:.1f}%)")
    
    print(f"\nClass distribution:")
    for col in ['Family_Desc', 'Main_Desc']:
        print(f"\n  --- {col} ---")
        counts = df[col].value_counts()
        for cat, cnt in counts.head(15).items():
            print(f"    {cat}: {cnt}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    print("="*60)
    print(" ENHANCED DATA AUGMENTATION")
    print("="*60)
    
    print("\nLoading dataset...")
    df = pd.read_excel(INPUT_FILE)
    
    analyze_dataset(df, "Original Dataset")
    
    # Step 1: Fill missing values
    print("\n" + "="*60)
    print(" Step 1: Filling Missing Values")
    print("="*60)
    df = fill_missing_values(df)
    
    analyze_dataset(df, "After Filling Missing Values")
    
    # Step 2: Generate template-based samples
    print("\n" + "="*60)
    print(" Step 2: Generating Template-Based Samples")
    print("="*60)
    template_df = generate_template_based_samples(df)
    df = pd.concat([df, template_df], ignore_index=True)
    
    analyze_dataset(df, "After Template Generation")
    
    # Step 3: Augment underrepresented classes
    print("\n" + "="*60)
    print(" Step 3: Augmenting Underrepresented Classes")
    print("="*60)
    df = augment_underrepresented_classes(df)
    
    analyze_dataset(df, "Final Augmented Dataset")
    
    # Save
    print(f"\nSaving augmented dataset to {OUTPUT_FILE}...")
    df.to_excel(OUTPUT_FILE, index=False)
    print("Done!")
    
    return df


if __name__ == "__main__":
    df = main()
