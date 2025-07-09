from typing import List
from sentence_transformers import SentenceTransformer
import numpy as np

class EmbeddingModel:
    """
    Loads a sentence-transformers embedding model and provides a method to embed text(s) into vectors.
    """
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Loads the embedding model.
        """
        self.model = SentenceTransformer(model_name)

    def embed(self, texts: List[str]) -> np.ndarray:
        """
        Given a list of strings, returns their embeddings as a NumPy array.
        """
        embeddings = self.model.encode(texts, show_progress_bar=False, convert_to_numpy=True, normalize_embeddings=True)
        return embeddings 