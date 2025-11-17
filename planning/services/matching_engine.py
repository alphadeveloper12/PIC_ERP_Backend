# core/planning/services/matching_engine.py

from planning.models import P6Activity, MappingResult
from estimation.models import BOQItem

class MatchingEngine:

    @staticmethod
    def match_and_save(boq_df, p6_df):
        results = []

        for _, boq in boq_df.iterrows():
            best = None
            best_score = 0

            for _, p6 in p6_df.iterrows():
                score = 0

                # WBS code matching
                if boq["code"] and boq["code"][1:].lower() in str(p6["wbs_code"]).lower():
                    score += 0.40

                # Keyword match
                if any(w.lower() in p6["activity_name"].lower() for w in boq["description"].split()):
                    score += 0.20

                # Semantic similarity
                sem = semantic_similarity(boq["description"], p6["activity_name"])
                score += sem * 0.40

                if score > best_score:
                    best = p6
                    best_score = score

            # Save only if best match exists
            if best is not None:
                MappingResult.objects.update_or_create(
                    boq=BOQItem.objects.get(id=boq["id"]),
                    p6=P6Activity.objects.get(task_id=best["task_id"]),
                    defaults={"confidence": best_score}
                )

            results.append({
                "boq_description": boq["description"],
                "boq_code": boq["code"],
                "matched_activity": best["activity_name"] if best is not None else None,
                "task_id": best["task_id"] if best is not None else None,
                "confidence": best_score
            })

        return results
