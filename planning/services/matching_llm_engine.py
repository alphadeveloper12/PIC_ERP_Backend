# planning/services/matching_llm_engine.py

import chromadb
from sentence_transformers import SentenceTransformer
from planning.models import MappingResult, P6Activity
from django.db import transaction
import logging
from tqdm import tqdm

logger = logging.getLogger(__name__)

model = SentenceTransformer("all-MiniLM-L6-v2")   # 384d fast model


class LLMMatchingEngine:

    def __init__(self):
        self.chroma = chromadb.PersistentClient(path=".chroma")
        self.collection = self.chroma.get_collection("boq_items")

    def match_and_save(self, p6_df):
        logger.info("Starting SUPER FAST matching (no API calls).")

        activities = p6_df["activity_name"].tolist()

        # 👉 Embed ALL P6 activities in ONE SHOT (super fast)
        embeddings = model.encode(
            activities, 
            batch_size=256, 
            convert_to_numpy=True
        )

        # Query Chroma in batch
        search = self.collection.query(
            query_embeddings=embeddings.tolist(),
            n_results=1
        )

        mappings = []
        results = []

        for idx, row in enumerate(p6_df.itertuples()):
            match_text = search["documents"][idx][0]
            boq_id = search["metadatas"][idx][0]["boq_id"]

            p6_obj = P6Activity.objects.filter(task_id=row.task_id).first()

            if p6_obj:
                mappings.append(MappingResult(
                    boq_id=boq_id,
                    p6=p6_obj,
                    confidence=1.0
                ))

                results.append({
                    "p6_activity": row.activity_name,
                    "matched_boq": match_text,
                    "boq_id": boq_id,
                    "confidence": 1.0
                })

        # Save quickly
        with transaction.atomic():
            MappingResult.objects.all().delete()
            MappingResult.objects.bulk_create(mappings, batch_size=5000)

        logger.info(f"FAST matching completed. {len(results)} items matched.")
        return results
