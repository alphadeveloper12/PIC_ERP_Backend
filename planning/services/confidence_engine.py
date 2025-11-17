# core/planning/services/confidence_engine.py

def classify_confidence(score):
    if score >= 0.85:
        return "AUTO_MATCH"
    if score >= 0.65:
        return "REVIEW"
    return "UNMATCHED"
