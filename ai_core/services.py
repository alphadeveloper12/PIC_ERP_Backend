import os
import torch
import warnings
from sentence_transformers import SentenceTransformer

# Suppress warnings
warnings.filterwarnings("ignore")

class EmbeddingService:
    """
    Singleton service to load the SBERT model once and provide embedding capabilities.
    Running completely locally on CPU (or GPU if available).
    """
    _instance = None
    _model = None
    
    # Model name - small and fast for CPU usage
    MODEL_NAME = 'all-MiniLM-L6-v2' 

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            cls._instance._load_model()
        return cls._instance

    def _load_model(self):
        print(f"Loading SBERT model: {self.MODEL_NAME}...")
        try:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            self._model = SentenceTransformer(self.MODEL_NAME, device=device)
            print(f"Model loaded successfully on {device}.")
        except Exception as e:
            print(f"Error loading SBERT model: {e}")
            raise

    def encode(self, text: str) -> list[float] | None:
        """
        Returns a list of floats representing the vector embedding of the text.
        
        Args:
            text (str): The input text to encode.
            
        Returns:
            list[float] | None: The embedding vector or None if input is empty.
        """
        if not text:
            return None
        
        # Ensure text is a string
        if not isinstance(text, str):
            text = str(text)
            
        embedding = self._model.encode(text)
        return embedding.tolist()

    def encode_batch(self, texts):
        """
        Encodes a list of texts. Returns list of vectors.
        """
        if not texts:
            return []
            
        embeddings = self._model.encode(texts)
        return embeddings.tolist()

# Global instance for easy import
embedding_service = EmbeddingService()
