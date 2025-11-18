# planning/services/chroma_setup.py
import chromadb
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")  # 384 dim, FAST

class ChromaBOQIndexer:
    def __init__(self):
        self.chroma = chromadb.PersistentClient(path=".chroma")
    
    def rebuild_index(self):
        # Clear old collection
        try:
            self.chroma.delete_collection("boq_items")
        except:
            pass
        
        collection = self.chroma.create_collection(
            name="boq_items",
            metadata={"hnsw:space": "cosine"}
        )

        from estimation.models import BOQItem
        boq_items = BOQItem.objects.all()

        texts = [i.description for i in boq_items]
        ids = [str(i.id) for i in boq_items]
        metadatas = [{"boq_id": i.id} for i in boq_items]

        # Generate embeddings in one batch (FAST)
        embeddings = model.encode(texts, batch_size=256, convert_to_numpy=True)

        collection.add(
            documents=texts,
            ids=ids,
            metadatas=metadatas,
            embeddings=embeddings.tolist()
        )

        print("BOQ Index Rebuilt Successfully")
