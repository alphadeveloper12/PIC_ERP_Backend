import pandas as pd
import numpy as np
import re
import os
import joblib
from django.conf import settings

class ERCModel:
    """
    ERC Model class that handles rule-based and ML-based ERC code generation.
    """
    # ==========================================
    # CONFIGURATION
    # ==========================================
    PROJECT_CONFIG = {
        'VIDA': {
            'id': 'Vida',
            'cols': {'major': 'VDA Package / Scope', 'minor': 'VDA MEP Major Trades'},
        },
        'RIVERA': {
            'id': 'Rivera',
            'cols': {'major': 'RIVERA-Major Trades', 'minor': 'RIVERA-BOQ L02'},
        },
        'MONTURA': {
            'id': 'Montura',
            'cols': {'major': 'PIC-Major Trades', 'minor': 'PIC-BOQL02'},
        },
        'ALANA': {
            'id': 'Alana',
            'cols': {'major': None, 'minor': None},
        }
    }

    DISC_RULES = {
        'MEP': ['mep', 'elec', 'mech', 'hvac', 'plumb', 'pipe', 'duct', 'wire', 'cable', 'drain', 'water', 'fcu', 'chiller',
                'lighting', 'power', 'sanitary', 'dewa'],
        'PRE': ['fence', 'hoist', 'crane', 'site office', 'security', 'signage', 'mobilization', 'demobilization',
                'preliminaries', 'temporary', 'scaffold'],
        'LND': ['landscap', 'irrigation', 'planting', 'pool', 'hardscape', 'softscape', 'external works'],
        'CIV': ['excavat', 'backfill', 'grade', 'leveling', 'dewater', 'pile', 'shor', 'earth', 'site work', 'ground',
                'dm '],
        'STR': ['post tension', 'post-tension', ' pt ', 'tendon', 'stressing', 'grouting', 'concrete', 'conc', 'steel',
                'rebar', 'formwork', 'shutter', 'pour', 'cast', 'raft', 'slab', 'column', 'beam', 'hollow core', 'precast',
                'panel', 'superstructure', 'substructure'],
        'ARC': ['block', 'plaster', 'paint', 'tile', 'floor', 'ceiling', 'door', 'window', 'facade', 'cladding', 'finish',
                'waterproof', 'joinery', 'internal finish']
    }

    TRADE_RULES = {
        'ATH': ['noc', 'authority', 'dewa', 'dcd', ' dm ', 'rta', 'municipality', 'civil defence', 'approvals'],
        'PT': ['post tension', 'post-tension', 'tendon', 'stressing', 'grouting'],
        'CIS': ['pour', 'cast', 'situ', 'formwork', 'shutter', 'rebar', 'fixing steel', 'concrete works'],
        'PC': ['precast', 'hollow core', 'panel', 'erection'],
        'MOS': ['method statement', 'mos ', ' mos', 'procedure'],
        'MAS': ['block', 'masonry'],
        'FIN': ['paint', 'tile', 'plaster', 'screed', 'ceramic', 'porcelain', 'ceiling', 'floor', 'joinery', 'wood'],
        'WPR': ['waterproof', 'insulation', 'roofing'],
        'ELE': ['elec', 'wire', 'cable', 'db', 'containment', 'pulling', 'terminat', 'lv', 'mv', 'earthing'],
        'PLM': ['plumb', 'pipe', 'drain', 'water', 'valve', 'sanitary', 'sewerage'],
        'VAC': ['hvac', 'duct', 'ac', 'fcu', 'chiller', 'air', 'ventilation'],
        'FF': ['fire', 'alarm', 'fighting', 'sprinkler']
    }

    ACTIVITY_RULES = {
        'TIL': ['tile', 'ceramic', 'porcelain', 'marble', 'granite', 'skirting'],
        'PNT': ['paint', 'coat', 'primer', 'emulsion'],
        'CEL': ['ceiling', 'gypsum', 'false ceiling', 'grid'],
        'PLA': ['plaster', 'render'],
        'JON': ['joinery', 'wood', 'door', 'wardrobe', 'cabinet', 'kitchen', 'vanity'],
        'FLR': ['flooring', 'screed', 'epoxy', 'parquet', 'carpet'],
        'FRM': ['formwork', 'shutter', 'mould'],
        'REB': ['rebar', 'steel', 'reinforcement', 'mesh', 'cage'],
        'POU': ['pour', 'cast', 'concrete', 'placing'],
        'CUR': ['cur', 'repair'],
        'FIX': ['first fix', '2nd fix', 'final fix', 'installation', 'install'],
        'TST': ['test', 'commission', 'pressure', 'continuity', 'megger'],
        'WIR': ['wire', 'cabling', 'pulling', 'termination', 'dressing'],
        'DUC': ['duct', 'insulation', 'vcd', 'vav', 'grille', 'diffuser'],
        'SUB': ['submit', 'submission', 'apply', 'application'],
        'APP': ['approv', 'obtain', 'received'],
        'NOC': ['noc', 'certificate', 'permit'],
        'INS': ['inspect']
    }

    def __init__(self, model_path=None, vectorizer_path=None):
        base_dir = settings.BASE_DIR
        self.model_path = model_path or os.path.join(base_dir, 'erc_model', 'erc_model.joblib')
        self.vectorizer_path = vectorizer_path or os.path.join(base_dir, 'erc_model', 'erc_vectorizer.joblib')
        self.model = None
        self.vectorizer = None

    def determine_phase(self, full_text):
        full_text = full_text.lower()
        pmg_keywords = ['commencement', 'completion', 'possession', 'notice to', 'duration', 'milestone', 'key date',
                        'taking over', 'handing over']
        if any(k in full_text for k in pmg_keywords): return 'PMG'

        qac_keywords = ['method statement', 'mos ', ' mos', 'inspection', 'itp', 'qcp', 'quality', 'audit']
        if any(k in full_text for k in qac_keywords): return 'QAC'

        eng_strong = ['noc', 'authority', 'ath ', ' ath', 'submit', 'submittal', 'submission', 'approv', 'shop drawing',
                      'design', 'calc', 'rfi', 'ifc', 'pre-qual', 'drawing', 'dwg', 's/d', 'transmittal']
        if any(k in full_text for k in eng_strong): return 'ENG'

        eng_weak = ['sample', 'prototype', 'mockup', 'mock-up', 'technical data', 'compliance', 'brochure', 'dewa', 'dcd',
                    ' dm ']
        execution_verbs = ['install', 'construct', 'build', 'fix', 'erect', 'cast', 'pour', 'apply', 'execution',
                           'connection']
        if any(k in full_text for k in eng_weak):
            if not any(v in full_text for v in execution_verbs): return 'ENG'

        hnd_keywords = ['snag', 'clean', 'handover', 'toc', 'testing', 'commission']
        if any(k in full_text for k in hnd_keywords): return 'HND'

        prc_keywords = ['order', 'deliver', 'fabricat', 'lpo', 'procurement', 'material', 'shipping']
        if any(k in full_text for k in prc_keywords): return 'PRC'
        if 'supply' in full_text:
            noun_exclusions = ['water', 'power', 'elec', 'air', 'chain', 'duct', 'pipe']
            is_noun = any(exc in full_text for exc in noun_exclusions)
            is_action = any(v in full_text for v in execution_verbs)
            if not is_noun and not is_action: return 'PRC'

        return 'CN'

    def decode_activity_id(self, act_id):
        if pd.isna(act_id): return None
        tokens = re.split(r'[-_ ]', str(act_id).upper())
        if 'NOC' in tokens: return 'SIGNAL_NOC'
        if 'ATH' in tokens: return 'SIGNAL_ATH'
        if 'STR' in tokens or 'ST' in tokens: return 'STR'
        if 'ARC' in tokens or 'AR' in tokens: return 'ARC'
        if 'MEP' in tokens: return 'MEP'
        if 'CIV' in tokens: return 'CIV'
        if 'LND' in tokens or 'LS' in tokens: return 'LND'
        return None

    def generate_erc_code(self, row, config=None):
        """
        Generates ERC code using rule-based logic.
        If config is provided, it uses the major/minor columns from the row.
        """
        act_name_raw = row.get('Activity Name', '')
        if pd.isna(act_name_raw) or str(act_name_raw).strip() == '': return "WBS-SUM-GEN-GEN"
        act_name = str(act_name_raw).lower()
        act_id = row.get('Activity ID', '')

        major_cat = ""
        minor_cat = ""
        if config:
            major_cat = str(row.get(config['cols']['major'], '')).lower() if config['cols']['major'] else ""
            minor_cat = str(row.get(config['cols']['minor'], '')).lower() if config['cols']['minor'] else ""
        
        full_text = f"{act_name} {major_cat} {minor_cat}"

        phase = self.determine_phase(full_text)
        discipline = "GEN"
        trade = "GEN"

        id_signal = self.decode_activity_id(act_id)

        if id_signal == 'SIGNAL_NOC' or id_signal == 'SIGNAL_ATH':
            phase, discipline, trade = 'ENG', 'GEN', 'ATH'
        elif id_signal:
            discipline = id_signal

        if discipline == "GEN":
            for code, keywords in self.DISC_RULES.items():
                if any(k in full_text for k in keywords):
                    discipline = code
                    break

        if trade == "GEN":
            if 'noc' in full_text or 'authority' in full_text or ' ath' in full_text:
                trade = 'ATH'
            elif phase == 'QAC' and ('mos' in full_text or 'method' in full_text):
                trade = 'MOS'
            elif 'post tension' in full_text or 'tendon' in full_text:
                trade = 'PT'

            is_block_location = bool(re.search(r'block\s*[\[\d]', act_name)) if "block" in act_name else False
            if "block" in full_text and not is_block_location:
                if "work" in full_text or "wall" in full_text or "masonry" in full_text:
                    trade = "MAS"
                    discipline = "ARC" if discipline == "GEN" else discipline

            if trade == "GEN":
                for code, keywords in self.TRADE_RULES.items():
                    if any(k in full_text for k in keywords):
                        trade = code
                        break

        activity = "GEN"
        for code, keywords in self.ACTIVITY_RULES.items():
            if any(k in full_text for k in keywords):
                activity = code
                break

        if activity == "GEN":
            if "slab" in full_text:
                activity = "SLB"
            elif "col" in full_text:
                activity = "COL"
            elif "found" in full_text or "raft" in full_text:
                activity = "FND"
            elif "wall" in full_text:
                activity = "WLL"

        return f"{phase}-{discipline}-{trade}-{activity}"

    def load_model(self):
        """Loads the trained model and vectorizer from disk."""
        if os.path.exists(self.model_path) and os.path.exists(self.vectorizer_path):
            try:
                self.model = joblib.load(self.model_path)
                self.vectorizer = joblib.load(self.vectorizer_path)
                return True
            except Exception as e:
                print(f"Error loading model: {e}")
                return False
        return False

    def predict(self, activity_names):
        """Predicts ERC codes for a list of activity names using ML model."""
        if self.model is None or self.vectorizer is None:
            if not self.load_model():
                # Fallback to rule-based if ML model is not available
                return [self.generate_erc_code({'Activity Name': name}) for name in activity_names]
        
        try:
            X = self.vectorizer.transform(pd.Series(activity_names).astype(str))
            return self.model.predict(X)
        except Exception as e:
            print(f"Error during prediction: {e}")
            # Fallback to rule-based
            return [self.generate_erc_code({'Activity Name': name}) for name in activity_names]
