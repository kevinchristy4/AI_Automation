import numpy as np
from typing import List, Dict, Any, Tuple
from .vector_ranker import VectorRanker

class VectorDatabase:
    """
    Stores element vectors and their mappings to DOM elements. Provides a search method for cosine similarity.
    Now uses VectorRanker internally for consistent ranking logic.
    """
    def __init__(self, vectors: np.ndarray, elements: List[Dict[str, Any]], embedding_model=None):
        """
        vectors: np.ndarray of shape (n_elements, embedding_dim)
        elements: List of original DOM element dicts
        embedding_model: EmbeddingModel instance for VectorRanker
        """
        self.vectors = vectors
        self.elements = elements
        self.embedding_model = embedding_model
        if embedding_model:
            self.vector_ranker = VectorRanker(embedding_model)
        else:
            self.vector_ranker = None

    def search(self, query_vector: np.ndarray) -> Tuple[int, float]:
        """
        Given a query vector, returns the index of the most similar element and the similarity score.
        Maintains backward compatibility with existing code.
        """
        if self.vector_ranker:
            # Use VectorRanker for consistent ranking
            candidates = self.vector_ranker.rank(self.elements, query_vector)
            if candidates:
                # Find the index of the top candidate in the original elements list
                top_candidate = candidates[0]
                for i, element in enumerate(self.elements):
                    if element.get('signature') == top_candidate.get('signature'):
                        return i, top_candidate['semantic_score']
            return 0, 0.0
        else:
            # Fallback to original logic if no embedding_model provided
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