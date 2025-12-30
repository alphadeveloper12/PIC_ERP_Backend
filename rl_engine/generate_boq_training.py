"""
BOQ-Style Training Data Generator

This script creates training samples that match BOQ description patterns
(short material/work descriptions) rather than activity descriptions.
"""

import pandas as pd
import numpy as np
import random

OUTPUT_FILE = "inputs/boq_training_data.xlsx"

# ============================================================================
# BOQ-STYLE TRAINING DATA
# Each entry: (description, Level1, Level2, Level3, Family, Main)
# Level1 categories:
#   - Construction: Physical building work (concrete, structural, installation)
#   - Shop Drawing: Design/drawing submissions
#   - Method Statements: Work procedure submissions
#   - General: Section headers, project management
# ============================================================================

BOQ_TRAINING_DATA = [
    # STRUCTURAL WORKS - Construction work items
    ("Footings", "Construction", "Structure", "Work Execution", "Structural Works", "Not Applicable"),
    ("Foundation", "Construction", "Structure", "Work Execution", "Structural Works", "Not Applicable"),
    ("Pile cap", "Construction", "Structure", "Work Execution", "Structural Works", "Not Applicable"),
    ("Grade beam", "Construction", "Structure", "Work Execution", "Structural Works", "Not Applicable"),
    ("Tie beam", "Construction", "Structure", "Work Execution", "Structural Works", "Not Applicable"),
    ("Tie beams", "Construction", "Structure", "Work Execution", "Structural Works", "Not Applicable"),
    ("Columns", "Construction", "Structure", "Work Execution", "Structural Works", "Not Applicable"),
    ("Column reinforcement", "Construction", "Structure", "Work Execution", "Structural Works", "Not Applicable"),
    ("Beams", "Construction", "Structure", "Work Execution", "Structural Works", "Not Applicable"),
    ("Beam reinforcement", "Construction", "Structure", "Work Execution", "Structural Works", "Not Applicable"),
    ("Slab", "Construction", "Structure", "Work Execution", "Structural Works", "Not Applicable"),
    ("Suspended slab", "Construction", "Structure", "Work Execution", "Structural Works", "Not Applicable"),
    ("Ground floor slab", "Construction", "Structure", "Work Execution", "Structural Works", "Not Applicable"),
    ("First floor slab", "Construction", "Structure", "Work Execution", "Structural Works", "Not Applicable"),
    ("Roof slab", "Construction", "Structure", "Work Execution", "Structural Works", "Not Applicable"),
    ("Stairs", "Construction", "Structure", "Work Execution", "Structural Works", "Not Applicable"),
    ("Staircase", "Construction", "Structure", "Work Execution", "Structural Works", "Not Applicable"),
    ("Stair flight", "Construction", "Structure", "Work Execution", "Structural Works", "Not Applicable"),
    ("Sides of the steps", "Construction", "Structure", "Work Execution", "Structural Works", "Not Applicable"),
    ("Staircase soffit", "Construction", "Structure", "Work Execution", "Structural Works", "Not Applicable"),
    ("Retaining walls", "Construction", "Structure", "Work Execution", "Structural Works", "Not Applicable"),
    ("Retaining wall", "Construction", "Structure", "Work Execution", "Structural Works", "Not Applicable"),
    ("Upstand beam", "Construction", "Structure", "Work Execution", "Structural Works", "Not Applicable"),
    ("Blinding", "Construction", "Structure", "Work Execution", "Structural Works", "Not Applicable"),
    ("Concrete blinding", "Construction", "Structure", "Work Execution", "Structural Works", "Not Applicable"),
    ("Plain poured concrete", "Construction", "Structure", "Work Execution", "Structural Works", "Not Applicable"),
    ("Reinforced concrete", "Construction", "Structure", "Work Execution", "Structural Works", "Not Applicable"),
    ("Precast concrete", "Construction", "Structure", "Work Execution", "Structural Works", "Not Applicable"),
    ("Formwork", "Construction", "Structure", "Work Execution", "Structural Works", "Not Applicable"),
    ("Shoring", "Construction", "Structure", "Work Execution", "Structural Works", "Not Applicable"),
    ("Rebar", "Construction", "Structure", "Work Execution", "Structural Works", "Not Applicable"),
    ("Reinforcement", "Construction", "Structure", "Work Execution", "Structural Works", "Not Applicable"),
    ("Bar reinforcement", "Construction", "Structure", "Work Execution", "Structural Works", "Not Applicable"),
    
    # SITE WORK / EXTERNAL WORKS - Construction work
    ("Soil treatment", "Construction", "Architectural", "Work Execution", "External Works", "Not Applicable"),
    ("To horizontal areas", "Construction", "Architectural", "Work Execution", "External Works", "Not Applicable"),
    ("To vertical areas", "Construction", "Architectural", "Work Execution", "External Works", "Not Applicable"),
    ("Excavation", "Construction", "Structure", "Work Execution", "External Works", "Not Applicable"),
    ("Excavation in all materials", "Construction", "Structure", "Work Execution", "External Works", "Not Applicable"),
    ("Backfilling", "Construction", "Structure", "Work Execution", "External Works", "Not Applicable"),
    ("Filled to excavation", "Construction", "Structure", "Work Execution", "External Works", "Not Applicable"),
    ("Carting away", "Construction", "Structure", "Work Execution", "External Works", "Not Applicable"),
    ("Removal of excavated material", "Construction", "Structure", "Work Execution", "External Works", "Not Applicable"),
    ("Surplus material", "Construction", "Structure", "Work Execution", "External Works", "Not Applicable"),
    ("Paving", "Construction", "Architectural", "Work Execution", "External Works", "Boundary Walls & Fencing"),
    ("Interlock pavers", "Construction", "Architectural", "Work Execution", "External Works", "Boundary Walls & Fencing"),
    ("80mm thick interlock pavers", "Construction", "Architectural", "Work Execution", "External Works", "Boundary Walls & Fencing"),
    ("Boundary wall", "Construction", "Architectural", "Work Execution", "External Works", "Boundary Walls & Fencing"),
    ("Precast boundary wall", "Construction", "Architectural", "Work Execution", "External Works", "Boundary Walls & Fencing"),
    ("200mm thick boundary wall", "Construction", "Architectural", "Work Execution", "External Works", "Boundary Walls & Fencing"),
    ("Fence", "Construction", "Architectural", "Work Execution", "External Works", "Boundary Walls & Fencing"),
    ("Fencing", "Construction", "Architectural", "Work Execution", "External Works", "Boundary Walls & Fencing"),
    ("Metal fence", "Construction", "Architectural", "Work Execution", "External Works", "Boundary Walls & Fencing"),
    ("Gates", "Construction", "Architectural", "Work Execution", "External Works", "Boundary Walls & Fencing"),
    ("Entrance gate", "Construction", "Architectural", "Work Execution", "External Works", "Boundary Walls & Fencing"),
    ("Landscaping", "Construction", "Architectural", "Work Execution", "External Works", "Not Applicable"),
    ("Soft landscaping", "Construction", "Architectural", "Work Execution", "External Works", "Not Applicable"),
    ("Hard landscaping", "Construction", "Architectural", "Work Execution", "External Works", "Not Applicable"),
    
    # DOORS & WINDOWS - Construction installation
    ("Doors", "Construction", "Architectural", "Work Execution", "Internal Finishes", "Doors & Windows"),
    ("Door", "Construction", "Architectural", "Work Execution", "Internal Finishes", "Doors & Windows"),
    ("Wooden door", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Doors & Windows"),
    ("Wooden doors", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Doors & Windows"),
    ("Timber door", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Doors & Windows"),
    ("Aluminum door", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Doors & Windows"),
    ("Aluminum doors", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Doors & Windows"),
    ("Glass door", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Doors & Windows"),
    ("Entrance door", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Doors & Windows"),
    ("Fire rated door", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Doors & Windows"),
    ("Internal door", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Doors & Windows"),
    ("External door", "Shop Drawing", "Architectural", "Submission", "External Finishes", "Doors & Windows"),
    ("Windows", "Shop Drawing", "Architectural", "Submission", "External Finishes", "Doors & Windows"),
    ("Window", "Shop Drawing", "Architectural", "Submission", "External Finishes", "Doors & Windows"),
    ("Aluminum window", "Shop Drawing", "Architectural", "Submission", "External Finishes", "Doors & Windows"),
    ("UPVC window", "Shop Drawing", "Architectural", "Submission", "External Finishes", "Doors & Windows"),
    ("Glass window", "Shop Drawing", "Architectural", "Submission", "External Finishes", "Doors & Windows"),
    ("Sliding door", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Doors & Windows"),
    ("Louvers", "Shop Drawing", "Architectural", "Submission", "External Finishes", "Doors & Windows"),
    
    # CEILING / GYPSUM
    ("Ceiling", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Gypsum / Ceiling Works"),
    ("False ceiling", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Gypsum / Ceiling Works"),
    ("Gypsum ceiling", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Gypsum / Ceiling Works"),
    ("Gypsum board", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Gypsum / Ceiling Works"),
    ("Gypsum board ceiling", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Gypsum / Ceiling Works"),
    ("Drop ceiling", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Gypsum / Ceiling Works"),
    ("Suspended ceiling", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Gypsum / Ceiling Works"),
    ("Plasterboard", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Gypsum / Ceiling Works"),
    ("Plasterboard ceiling", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Gypsum / Ceiling Works"),
    ("Access panel", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Gypsum / Ceiling Works"),
    ("Ceiling access panel", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Gypsum / Ceiling Works"),
    ("Bulkhead", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Gypsum / Ceiling Works"),
    ("Cornice", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Gypsum / Ceiling Works"),
    
    # TILING
    ("Tiles", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Tiling Works"),
    ("Tiling", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Tiling Works"),
    ("Floor tiles", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Floor & Wall Tiling Works"),
    ("Floor tiling", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Floor & Wall Tiling Works"),
    ("Wall tiles", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Wall Tiling Works"),
    ("Wall tiling", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Wall Tiling Works"),
    ("Ceramic tiles", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Tiling Works"),
    ("Porcelain tiles", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Tiling Works"),
    ("Bathroom tiles", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Floor & Wall Tiling Works"),
    ("Kitchen tiles", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Floor & Wall Tiling Works"),
    ("Mosaic tiles", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Tiling Works"),
    ("Marble tiles", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Tiling Works"),
    ("Granite tiles", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Tiling Works"),
    
    # PAINTING
    ("Paint", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Painting Works"),
    ("Painting", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Painting Works"),
    ("Internal paint", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Painting Works"),
    ("External paint", "Shop Drawing", "Architectural", "Submission", "External Finishes", "Painting Works"),
    ("Emulsion paint", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Painting Works"),
    ("Acrylic paint", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Painting Works"),
    ("Primer", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Painting Works"),
    ("Undercoat", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Painting Works"),
    ("Finish coat", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Painting Works"),
    
    # PLASTERING
    ("Plaster", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Plaster Works"),
    ("Plastering", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Plaster Works"),
    ("Internal plaster", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Plaster Works"),
    ("External plaster", "Shop Drawing", "Architectural", "Submission", "External Finishes", "Plaster Works"),
    ("Cement plaster", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Plaster Works"),
    ("Render", "Shop Drawing", "Architectural", "Submission", "External Finishes", "Plaster Works"),
    ("Rendering", "Shop Drawing", "Architectural", "Submission", "External Finishes", "Plaster Works"),
    
    # SCREED
    ("Screed", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Screed Works"),
    ("Floor screed", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Screed Works"),
    ("Cement screed", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Screed Works"),
    ("Leveling screed", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Screed Works"),
    ("Sand cement screed", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Screed Works"),
    
    # WATERPROOFING
    ("Waterproofing", "Shop Drawing", "Architectural", "Submission", "External Finishes", "Waterproofing Works"),
    ("Waterproof membrane", "Shop Drawing", "Architectural", "Submission", "External Finishes", "Waterproofing Works"),
    ("Bituminous waterproofing", "Shop Drawing", "Architectural", "Submission", "External Finishes", "Waterproofing Works"),
    ("Roof waterproofing", "Shop Drawing", "Architectural", "Submission", "External Finishes", "Waterproofing Works"),
    ("Bathroom waterproofing", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Waterproofing Works"),
    ("Wet area waterproofing", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Waterproofing Works"),
    ("Damp proof membrane", "Shop Drawing", "Architectural", "Submission", "External Finishes", "Waterproofing Works"),
    ("DPM", "Shop Drawing", "Architectural", "Submission", "External Finishes", "Waterproofing Works"),
    
    # KITCHEN
    ("Kitchen cabinet", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Kitchen Units & Counters"),
    ("Kitchen cabinets", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Kitchen Units & Counters"),
    ("Kitchen unit", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Kitchen Units & Counters"),
    ("Kitchen units", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Kitchen Units & Counters"),
    ("Countertop", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Kitchen Units & Counters"),
    ("Counter top", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Kitchen Units & Counters"),
    ("Kitchen countertop", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Kitchen Units & Counters"),
    ("Kitchen sink", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Kitchen Units & Counters"),
    ("Pantry cabinet", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Kitchen Units & Counters"),
    
    # WARDROBES
    ("Wardrobe", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Wardrobes & Closets"),
    ("Wardrobes", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Wardrobes & Closets"),
    ("Built-in wardrobe", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Wardrobes & Closets"),
    ("Closet", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Wardrobes & Closets"),
    ("Walk-in closet", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Wardrobes & Closets"),
    ("Storage cabinet", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Wardrobes & Closets"),
    
    # BALCONY / BALUSTRADE
    ("Balcony", "Shop Drawing", "Architectural", "Submission", "External Finishes", "Balcony & Balustrade Works"),
    ("Balcony railing", "Shop Drawing", "Architectural", "Submission", "External Finishes", "Balcony & Balustrade Works"),
    ("Balustrade", "Shop Drawing", "Architectural", "Submission", "External Finishes", "Balcony & Balustrade Works"),
    ("Glass balustrade", "Shop Drawing", "Architectural", "Submission", "External Finishes", "Balcony & Balustrade Works"),
    ("Metal railing", "Shop Drawing", "Architectural", "Submission", "External Finishes", "Balcony & Balustrade Works"),
    ("Handrail", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Balcony & Balustrade Works"),
    ("Stair railing", "Shop Drawing", "Architectural", "Submission", "Internal Finishes", "Balcony & Balustrade Works"),
    ("Guardrail", "Shop Drawing", "Architectural", "Submission", "External Finishes", "Balcony & Balustrade Works"),
    
    # FACADE / ELEVATION
    ("Facade", "Shop Drawing", "Architectural", "Submission", "External Finishes", "Elevation / Façade Works"),
    ("Elevation", "Shop Drawing", "Architectural", "Submission", "External Finishes", "Elevation / Façade Works"),
    ("External facade", "Shop Drawing", "Architectural", "Submission", "External Finishes", "Elevation / Façade Works"),
    ("Cladding", "Shop Drawing", "Architectural", "Submission", "External Finishes", "Elevation / Façade Works"),
    ("ACP cladding", "Shop Drawing", "Architectural", "Submission", "External Finishes", "Elevation / Façade Works"),
    ("GRC panels", "Shop Drawing", "Architectural", "Submission", "External Finishes", "Elevation / Façade Works"),
    ("Curtain wall", "Shop Drawing", "Architectural", "Submission", "External Finishes", "Elevation / Façade Works"),
    ("Precast panels", "Shop Drawing", "Architectural", "Submission", "External Finishes", "Elevation / Façade Works"),
    
    # ELECTRICAL
    ("Electrical wiring", "Shop Drawing", "MEP related items", "Submission", "Electrical Power & Lighting", "Electrical Power Works"),
    ("Electrical conduit", "Shop Drawing", "MEP related items", "Submission", "Electrical Power & Lighting", "Electrical Power Works"),
    ("Cable", "Shop Drawing", "MEP related items", "Submission", "Electrical Power & Lighting", "Electrical Power Works"),
    ("Cables", "Shop Drawing", "MEP related items", "Submission", "Electrical Power & Lighting", "Electrical Power Works"),
    ("Power cable", "Shop Drawing", "MEP related items", "Submission", "Electrical Power & Lighting", "Electrical Power Works"),
    ("Distribution board", "Shop Drawing", "MEP related items", "Submission", "Electrical Power & Lighting", "Electrical Power Works"),
    ("DB", "Shop Drawing", "MEP related items", "Submission", "Electrical Power & Lighting", "Electrical Power Works"),
    ("Main panel", "Shop Drawing", "MEP related items", "Submission", "Electrical Power & Lighting", "Electrical Power Works"),
    ("Switch", "Shop Drawing", "MEP related items", "Submission", "Electrical Power & Lighting", "Electrical Power Works"),
    ("Switches", "Shop Drawing", "MEP related items", "Submission", "Electrical Power & Lighting", "Electrical Power Works"),
    ("1Gang switch", "Shop Drawing", "MEP related items", "Submission", "Electrical Power & Lighting", "Electrical Power Works"),
    ("2Gang switch", "Shop Drawing", "MEP related items", "Submission", "Electrical Power & Lighting", "Electrical Power Works"),
    ("Socket", "Shop Drawing", "MEP related items", "Submission", "Electrical Power & Lighting", "Electrical Power Works"),
    ("Socket outlet", "Shop Drawing", "MEP related items", "Submission", "Electrical Power & Lighting", "Electrical Power Works"),
    ("Power socket", "Shop Drawing", "MEP related items", "Submission", "Electrical Power & Lighting", "Electrical Power Works"),
    ("ECC cable", "Shop Drawing", "MEP related items", "Submission", "Electrical Power & Lighting", "Electrical Power Works"),
    
    # LIGHTING
    ("Light fixture", "Shop Drawing", "MEP related items", "Submission", "Electrical Power & Lighting", "Lighting Works"),
    ("Light fixtures", "Shop Drawing", "MEP related items", "Submission", "Electrical Power & Lighting", "Lighting Works"),
    ("Lighting", "Shop Drawing", "MEP related items", "Submission", "Electrical Power & Lighting", "Lighting Works"),
    ("Downlight", "Shop Drawing", "MEP related items", "Submission", "Electrical Power & Lighting", "Lighting Works"),
    ("Spot light", "Shop Drawing", "MEP related items", "Submission", "Electrical Power & Lighting", "Lighting Works"),
    ("LED light", "Shop Drawing", "MEP related items", "Submission", "Electrical Power & Lighting", "Lighting Works"),
    ("Ceiling light", "Shop Drawing", "MEP related items", "Submission", "Electrical Power & Lighting", "Lighting Works"),
    ("Wall light", "Shop Drawing", "MEP related items", "Submission", "Electrical Power & Lighting", "Lighting Works"),
    ("Exterior light", "Shop Drawing", "MEP related items", "Submission", "Electrical Power & Lighting", "Lighting Works"),
    ("Garden light", "Shop Drawing", "MEP related items", "Submission", "Electrical Power & Lighting", "Lighting Works"),
    
    # PLUMBING / DRAINAGE
    ("Pipes", "Shop Drawing", "MEP related items", "Submission", "Plumbing & Drainage Family", "Drainage Works"),
    ("Pipe", "Shop Drawing", "MEP related items", "Submission", "Plumbing & Drainage Family", "Drainage Works"),
    ("UPVC pipe", "Shop Drawing", "MEP related items", "Submission", "Plumbing & Drainage Family", "Drainage Works"),
    ("PVC pipe", "Shop Drawing", "MEP related items", "Submission", "Plumbing & Drainage Family", "Drainage Works"),
    ("HDPE pipe", "Shop Drawing", "MEP related items", "Submission", "Plumbing & Drainage Family", "Drainage Works"),
    ("Drainage pipe", "Shop Drawing", "MEP related items", "Submission", "Plumbing & Drainage Family", "Drainage Works"),
    ("Waste pipe", "Shop Drawing", "MEP related items", "Submission", "Plumbing & Drainage Family", "Drainage Works"),
    ("Sewage pipe", "Shop Drawing", "MEP related items", "Submission", "Plumbing & Drainage Family", "Drainage Works"),
    ("Floor drain", "Shop Drawing", "MEP related items", "Submission", "Plumbing & Drainage Family", "Drainage Works"),
    ("Gully trap", "Shop Drawing", "MEP related items", "Submission", "Plumbing & Drainage Family", "Drainage Works"),
    ("Dry gully trap", "Shop Drawing", "MEP related items", "Submission", "Plumbing & Drainage Family", "Drainage Works"),
    ("DGT", "Shop Drawing", "MEP related items", "Submission", "Plumbing & Drainage Family", "Drainage Works"),
    ("Manhole", "Shop Drawing", "MEP related items", "Submission", "Plumbing & Drainage Family", "Drainage Works"),
    ("Inspection chamber", "Shop Drawing", "MEP related items", "Submission", "Plumbing & Drainage Family", "Drainage Works"),
    ("Water tank", "Shop Drawing", "MEP related items", "Submission", "Plumbing & Drainage Family", "Drainage Works"),
    ("Water supply", "Shop Drawing", "MEP related items", "Submission", "Plumbing & Drainage Family", "Drainage Works"),
    ("Water meter", "Shop Drawing", "MEP related items", "Submission", "Plumbing & Drainage Family", "Drainage Works"),
    
    # SANITARY
    ("WC", "Shop Drawing", "MEP related items", "Submission", "Plumbing & Drainage Family", "Sanitary Fixtures & Accessories"),
    ("Toilet", "Shop Drawing", "MEP related items", "Submission", "Plumbing & Drainage Family", "Sanitary Fixtures & Accessories"),
    ("Basin", "Shop Drawing", "MEP related items", "Submission", "Plumbing & Drainage Family", "Sanitary Fixtures & Accessories"),
    ("Wash basin", "Shop Drawing", "MEP related items", "Submission", "Plumbing & Drainage Family", "Sanitary Fixtures & Accessories"),
    ("Sink", "Shop Drawing", "MEP related items", "Submission", "Plumbing & Drainage Family", "Sanitary Fixtures & Accessories"),
    ("Shower", "Shop Drawing", "MEP related items", "Submission", "Plumbing & Drainage Family", "Sanitary Fixtures & Accessories"),
    ("Bathtub", "Shop Drawing", "MEP related items", "Submission", "Plumbing & Drainage Family", "Sanitary Fixtures & Accessories"),
    ("Bidet", "Shop Drawing", "MEP related items", "Submission", "Plumbing & Drainage Family", "Sanitary Fixtures & Accessories"),
    ("Faucet", "Shop Drawing", "MEP related items", "Submission", "Plumbing & Drainage Family", "Sanitary Fixtures & Accessories"),
    ("Tap", "Shop Drawing", "MEP related items", "Submission", "Plumbing & Drainage Family", "Sanitary Fixtures & Accessories"),
    ("Mixer", "Shop Drawing", "MEP related items", "Submission", "Plumbing & Drainage Family", "Sanitary Fixtures & Accessories"),
    ("Sanitary fittings", "Shop Drawing", "MEP related items", "Submission", "Plumbing & Drainage Family", "Sanitary Fixtures & Accessories"),
    ("Sanitary accessories", "Shop Drawing", "MEP related items", "Submission", "Plumbing & Drainage Family", "Sanitary Fixtures & Accessories"),
    ("Towel rail", "Shop Drawing", "MEP related items", "Submission", "Plumbing & Drainage Family", "Sanitary Fixtures & Accessories"),
    ("Mirror cabinet", "Shop Drawing", "MEP related items", "Submission", "Plumbing & Drainage Family", "Sanitary Fixtures & Accessories"),
    
    # GAS / LPG
    ("Gas pipe", "Shop Drawing", "MEP related items", "Submission", "Gas / LPG System", "LPG / Gas Works"),
    ("Gas piping", "Shop Drawing", "MEP related items", "Submission", "Gas / LPG System", "LPG / Gas Works"),
    ("LPG pipe", "Shop Drawing", "MEP related items", "Submission", "Gas / LPG System", "LPG / Gas Works"),
    ("LPG piping", "Shop Drawing", "MEP related items", "Submission", "Gas / LPG System", "LPG / Gas Works"),
    ("Gas meter", "Shop Drawing", "MEP related items", "Submission", "Gas / LPG System", "LPG / Gas Works"),
    ("Gas valve", "Shop Drawing", "MEP related items", "Submission", "Gas / LPG System", "LPG / Gas Works"),
    ("Gas regulator", "Shop Drawing", "MEP related items", "Submission", "Gas / LPG System", "LPG / Gas Works"),
    ("Gas point", "Shop Drawing", "MEP related items", "Submission", "Gas / LPG System", "LPG / Gas Works"),
    ("Kitchen gas", "Shop Drawing", "MEP related items", "Submission", "Gas / LPG System", "LPG / Gas Works"),
    
    # HVAC - Construction installation (Not Applicable for Main_Desc)
    ("AC unit", "Construction", "MEP related items", None, "HVAC Systems Family", "Not Applicable"),
    ("Air conditioning", "Construction", "MEP related items", None, "HVAC Systems Family", "Not Applicable"),
    ("Split unit", "Construction", "MEP related items", None, "HVAC Systems Family", "Not Applicable"),
    ("FCU", "Construction", "MEP related items", None, "HVAC Systems Family", "Not Applicable"),
    ("Fan coil unit", "Construction", "MEP related items", None, "HVAC Systems Family", "Not Applicable"),
    ("AHU", "Construction", "MEP related items", None, "HVAC Systems Family", "Not Applicable"),
    ("Ducting", "Construction", "MEP related items", None, "HVAC Systems Family", "Not Applicable"),
    ("AC ducting", "Construction", "MEP related items", None, "HVAC Systems Family", "Not Applicable"),
    ("Ventilation", "Construction", "MEP related items", None, "HVAC Systems Family", "Not Applicable"),
    ("Exhaust fan", "Construction", "MEP related items", None, "HVAC Systems Family", "Not Applicable"),
    ("Fresh air", "Construction", "MEP related items", None, "HVAC Systems Family", "Not Applicable"),
    ("Chiller", "Construction", "MEP related items", None, "HVAC Systems Family", "Not Applicable"),
    ("Refrigerant pipe", "Construction", "MEP related items", None, "HVAC Systems Family", "Not Applicable"),
    
    # MEP GENERAL / BUILDERS WORK - Construction
    ("Sleeves", "Construction", "MEP related items", None, "MEP General", "Builders Work for MEP"),
    ("Core cutting", "Construction", "MEP related items", None, "MEP General", "Builders Work for MEP"),
    ("MEP openings", "Construction", "MEP related items", None, "MEP General", "Builders Work for MEP"),
    ("Service openings", "Construction", "MEP related items", None, "MEP General", "Builders Work for MEP"),
    ("Chasing", "Construction", "MEP related items", None, "MEP General", "Builders Work for MEP"),
    ("Recess", "Construction", "MEP related items", None, "MEP General", "Builders Work for MEP"),
    ("Fire alarm", "Construction", "MEP related items", None, "MEP General", "Not Applicable"),
    ("Smoke detector", "Construction", "MEP related items", None, "MEP General", "Not Applicable"),
    ("Fire extinguisher", "Construction", "MEP related items", None, "MEP General", "Not Applicable"),
    
    # SECTION HEADERS (these should be General)
    ("SECTION B - SITE WORK", "General", "Architectural", None, None, None),
    ("SECTION C - CONCRETE WORK", "General", "Structure", None, None, None),
    ("SECTION D - MASONRY WORK", "General", "Architectural", None, None, None),
    ("B4 - SITE PREPARATION", "General", "Architectural", None, "External Works", None),
    ("B9 - EXCAVATION", "General", "Structure", None, "External Works", None),
    ("B11 - DISPOSAL", "General", "Structure", None, "External Works", None),
    ("B12 - FILLING", "General", "Structure", None, "External Works", None),
    ("B21 FENCING", "General", "Architectural", None, "External Works", "Boundary Walls & Fencing"),
    ("B22 - BOUNDARY WALL", "General", "Architectural", None, "External Works", "Boundary Walls & Fencing"),
]

def generate_variations(description, level1, level2, level3, family, main):
    """Generate variations of a description."""
    variations = []
    
    base_row = {
        'Activity_Description': description,
        'Level1_Desc': level1,
        'Level2_Desc': level2,
        'Level3_Desc': level3,
        'Family_Desc': family,
        'Main_Desc': main
    }
    variations.append(base_row)
    
    # Add variations
    suffixes = ['', ' (villa)', ' (GH)', ' - Type A', ' - Type B', ' works', ' installation']
    prefixes = ['Supply of ', 'Supply and fix ', 'Provide ', 'Install ', '']
    
    for suffix in suffixes[:3]:
        for prefix in prefixes[:2]:
            if prefix or suffix:
                new_desc = prefix + description + suffix
                if new_desc != description:
                    row = base_row.copy()
                    row['Activity_Description'] = new_desc
                    variations.append(row)
    
    return variations


def main():
    print("Generating BOQ-style training data...")
    
    all_rows = []
    
    for item in BOQ_TRAINING_DATA:
        desc, level1, level2, level3, family, main = item
        variations = generate_variations(desc, level1, level2, level3, family, main)
        all_rows.extend(variations)
    
    df = pd.DataFrame(all_rows)
    
    print(f"\nGenerated {len(df)} training samples")
    print("\nLevel1 distribution:")
    print(df['Level1_Desc'].value_counts())
    print("\nFamily distribution:")
    print(df['Family_Desc'].value_counts())
    print("\nMain distribution:")
    print(df['Main_Desc'].value_counts())
    
    df.to_excel(OUTPUT_FILE, index=False)
    print(f"\nSaved to {OUTPUT_FILE}")
    
    return df


if __name__ == "__main__":
    main()
