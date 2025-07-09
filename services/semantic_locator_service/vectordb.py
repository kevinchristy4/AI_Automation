import numpy as np
from typing import List, Dict, Any, Tuple

class VectorDatabase:
    """
    Stores element vectors and their mappings to DOM elements. Provides a search method for cosine similarity.
    """
    def __init__(self, vectors: np.ndarray, elements: List[Dict[str, Any]]):
        """
        vectors: np.ndarray of shape (n_elements, embedding_dim)
        elements: List of original DOM element dicts
        """
        self.vectors = vectors
        self.elements = elements

    def search(self, query_vector: np.ndarray) -> Tuple[int, float]:
        """
        Given a query vector, returns the index of the most similar element and the similarity score.
        """
        # Ensure query_vector is 1D
        if query_vector.ndim == 2:
            query_vector = query_vector[0]
        # Cosine similarity for normalized vectors is dot product
        similarities = np.dot(self.vectors, query_vector)
        best_idx = int(np.argmax(similarities))
        best_score = float(similarities[best_idx])
        return best_idx, best_score

    def get_similarities(self, query_vector: np.ndarray) -> np.ndarray:
        """
        Given a query vector, returns all similarity scores for debugging.
        """
        # Ensure query_vector is 1D
        if query_vector.ndim == 2:
            query_vector = query_vector[0]
        # Cosine similarity for normalized vectors is dot product
        return np.dot(self.vectors, query_vector) 