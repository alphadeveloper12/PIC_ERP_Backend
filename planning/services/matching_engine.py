# planning/services/matching_engine.py

from planning.models import P6Activity, MappingResult
from estimation.models import BOQItem
from sentence_transformers import SentenceTransformer, util
from django.db import transaction

import numpy as np
import pandas as pd

model = SentenceTransformer('all-MiniLM-L6-v2')


class MatchingEngine:

    @staticmethod
    def match_and_save(boq_df, p6_df):
        results = []

        # ------------------------------------
        # 1. Pre-encode semantic vectors
        # ------------------------------------
        boq_embeddings = model.encode(
            boq_df["description"].tolist(), convert_to_tensor=True, show_progress_bar=True
        )
        p6_embeddings = model.encode(
            p6_df["activity_name"].tolist(), convert_to_tensor=True, show_progress_bar=True
        )

        # Compute similarity matrix once
        semantic_matrix = util.cos_sim(boq_embeddings, p6_embeddings).cpu().numpy()

        # Convert P6 df to dict rows
        p6_records = p6_df.to_dict(orient="records")

        mapping_bulk = []

        # ------------------------------------
        # 2. Loop through BOQ rows only
        # ------------------------------------
        for i, boq in boq_df.iterrows():
            boq_words = boq["description"].lower().split()
            boq_code = str(boq["code"])[1:].lower() if boq["code"] else ""

            best_index = None
            best_score = -1

            for j, p6 in enumerate(p6_records):
                score = 0

                # WBS code match
                if boq_code and boq_code in str(p6["wbs_code"]).lower():
                    score += 0.40

                # Keyword match
                activity_l = p6["activity_name"].lower()
                if any(w in activity_l for w in boq_words):
                    score += 0.20

                # Semantic similarity
                score += semantic_matrix[i][j] * 0.40

                # Best match picking
                if score > best_score:
                    best_score = score
                    best_index = j

            matched = p6_records[best_index]

            # Append preview result
            results.append({
                "boq_description": boq["description"],
                "boq_code": boq["code"],
                "matched_activity": matched["activity_name"],
                "task_id": matched["task_id"],
                "confidence": best_score
            })

            # Prepare bulk mapping entry
            mapping_bulk.append(MappingResult(
                boq_id=boq["id"],
                p6_id=P6Activity.objects.filter(task_id=matched["task_id"])
                    .values_list("id", flat=True).first(),
                confidence=best_score
            ))

        # ------------------------------------
        # 3. Overwrite MappingResult
        # ------------------------------------
        MappingResult.objects.all().delete()

        with transaction.atomic():
            MappingResult.objects.bulk_create(mapping_bulk, batch_size=5000)

        return results
