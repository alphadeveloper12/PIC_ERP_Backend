import pandas as pd
import os
import json
from rl_feedback_loop import RLFeedbackHandler, PRIMAVERA_LINKS_PATH
from link_boq_primavera_rl import link_boq_primavera

def test_primavera_feedback():
    # 1. Setup mock data
    os.makedirs("inputs", exist_ok=True)
    os.makedirs("outputs", exist_ok=True)
    os.makedirs("models", exist_ok=True)
    
    # Mock BOQ with hierarchy
    boq_data = {
        'Item No': [None, None, None, 'A', 'B'],
        'Description': [
            'SECTION B - SITE WORK',
            'B4 - SITE PREPARATION',
            'Soil treatment',
            'To horizontal areas',
            'To vertical areas'
        ],
        'Unit': [None, None, None, 'm2', 'm2'],
        'Quantity': [None, None, None, 186, 377],
        'Rate': [None, None, None, None, None],
        'Amount': [None, None, None, 0, 0]
    }
    pd.DataFrame(boq_data).to_excel("inputs/test_boq_hierarchical.xlsx", index=False)
    
    # Mock Primavera
    prim_data = {
        'Activity ID': ['NH9-CN-IF-25290', 'NH9-CN-ST-001', 'NH9-CN-ST-002'],
        'Activity Name': ['Floor Tiling wet area -GH-', 'Anti -Termite Under footing', 'Anti -Termite Under SOG']
    }
    pd.DataFrame(prim_data).to_excel("inputs/test_prim_hierarchical.xlsx", index=False)
    
    # 2. Clear existing links for clean test
    if os.path.exists(PRIMAVERA_LINKS_PATH):
        os.remove(PRIMAVERA_LINKS_PATH)
    
    # 3. Apply feedback using combined context
    handler = RLFeedbackHandler()
    # Soil treatment + To horizontal areas
    handler.update_primavera_link('Soil treatment To horizontal areas', 'NH9-CN-ST-001')
    # Soil treatment + To vertical areas
    handler.update_primavera_link('Soil treatment To vertical areas', 'NH9-CN-ST-002')
    
    # 4. Run linking
    output_json = "outputs/test_linked_hierarchical.json"
    link_boq_primavera("inputs/test_boq_hierarchical.xlsx", "inputs/test_prim_hierarchical.xlsx", output_json)
    
    # 5. Verify results
    with open(output_json, 'r') as f:
        data = json.load(f)
    
    # Flatten items from JSON structure for verification
    items = []
    for section in data['sections']:
        for subsection in section['subsections']:
            items.extend(subsection['items'])
    
    print(f"\nVerification Results:")
    print(f"Total items in JSON: {len(items)}")
    
    # Check linked items
    # Item A: Soil treatment To horizontal areas
    # Find item and check its subsection title
    item_a_info = None
    item_b_info = None
    
    for section in data['sections']:
        for subsection in section['subsections']:
            for item in subsection['items']:
                if item['description'] == 'To horizontal areas':
                    item_a_info = (item, subsection.get('title'))
                if item['description'] == 'To vertical areas':
                    item_b_info = (item, subsection.get('title'))
    
    if item_a_info and item_a_info[0]['primavera_activities']:
        item_a, title_a = item_a_info
        best_match_a = item_a['primavera_activities'][0]['Activity_ID']
        print(f"Item A Matched ID: {best_match_a} (Expected: NH9-CN-ST-001)")
        print(f"Item A Subsection Title: {title_a} (Expected: Soil treatment)")
    else:
        best_match_a = None
        title_a = None
        print("Item A not found or no matches")

    if item_b_info and item_b_info[0]['primavera_activities']:
        item_b, title_b = item_b_info
        best_match_b = item_b['primavera_activities'][0]['Activity_ID']
        print(f"Item B Matched ID: {best_match_b} (Expected: NH9-CN-ST-002)")
        print(f"Item B Subsection Title: {title_b} (Expected: Soil treatment)")
    else:
        best_match_b = None
        title_b = None
        print("Item B not found or no matches")
    
    success = (len(items) == 2 and 
               best_match_a == 'NH9-CN-ST-001' and 
               best_match_b == 'NH9-CN-ST-002' and
               title_a == 'Soil treatment' and
               title_b == 'Soil treatment')
    
    if success:
        print("\nSUCCESS: Hierarchical linking and context-aware feedback verified in JSON!")
    else:
        print("\nFAILURE: Verification failed.")

if __name__ == "__main__":
    test_primavera_feedback()
