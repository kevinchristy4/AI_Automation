import numpy as np
from typing import List, Dict, Any, Tuple
from abc import ABC, abstractmethod

class RankingStrategy(ABC):
    """Abstract base class for ranking strategies"""
    
    @abstractmethod
    def rank(self, candidates: List[Dict], context: Any) -> List[Dict]:
        """
        Rank candidates based on the strategy
        
        Args:
            candidates: List of candidate elements to rank
            context: Context information for ranking (e.g., query embedding, user step)
            
        Returns:
            Ranked list of candidates with scores
        """
        pass

class VectorRanker(RankingStrategy):
    """
    Handles vector similarity search and ranking using cosine similarity.
    Extracted from VectorDatabase logic for better separation of concerns.
    """
    
    def __init__(self, embedding_model):
        self.embedding_model = embedding_model
        self.debug = False
    
    def set_debug(self, debug: bool):
        """Enable or disable debug output"""
        self.debug = debug
    
    def rank(self, candidates: List[Dict], query_embedding: np.ndarray) -> List[Dict]:
        """
        Rank candidates by vector similarity to the query
        
        Args:
            candidates: List of candidate elements with signatures
            query_embedding: Query vector to compare against
            
        Returns:
            Ranked list of candidates with semantic scores
        """
        if not candidates:
            return []
        
        # Extract signatures from candidates
        signatures = [candidate.get('signature', '') for candidate in candidates]
        
        # Embed the signatures
        signature_embeddings = self.embedding_model.embed(signatures)
        
        # Calculate similarities
        similarities = self._calculate_similarities(query_embedding, signature_embeddings)
        
        # Rank candidates by similarity
        ranked_candidates = self._rank_by_similarity(candidates, similarities)
        
        if self.debug:
            print(f"VectorRanker: Ranked {len(ranked_candidates)} candidates by similarity")
            for i, candidate in enumerate(ranked_candidates[:3]):
                print(f"  {i+1}. Score: {candidate['semantic_score']:.3f} | {candidate['signature'][:50]}...")
        
        return ranked_candidates
    
    def _calculate_similarities(self, query_embedding: np.ndarray, signature_embeddings: np.ndarray) -> np.ndarray:
        """
        Calculate cosine similarities between query and signature embeddings
        
        Args:
            query_embedding: Query vector
            signature_embeddings: Matrix of signature vectors
            
        Returns:
            Array of similarity scores
        """
        # Ensure query_embedding is 1D
        if query_embedding.ndim == 2:
            query_embedding = query_embedding[0]
        
        # Cosine similarity for normalized vectors is dot product
        similarities = np.dot(signature_embeddings, query_embedding)
        return similarities
    
    def _rank_by_similarity(self, candidates: List[Dict], similarities: np.ndarray, top_k: int = None) -> List[Dict]:
        """
        Rank candidates by similarity scores
        
        Args:
            candidates: List of candidate elements
            similarities: Array of similarity scores
            top_k: Number of top candidates to return (None for all)
            
        Returns:
            Ranked list of candidates with semantic scores
        """
        # Get top-k indices
        num_elements = len(similarities)
        
        if top_k is None or top_k >= num_elements:
            # Sort all elements
            top_indices = np.argsort(-similarities)
        else:
            # Use argpartition for efficiency
            top_indices = np.argpartition(-similarities, top_k)[:top_k]
            # Sort only the top_k results by score
            top_indices = top_indices[np.argsort(-similarities[top_indices])]
        
        # Convert to ranked candidates format
        ranked_candidates = []
        for idx in top_indices:
            # Skip negative similarity scores
            if similarities[idx] < 0:
                continue
                
            candidate = candidates[idx].copy()
            candidate['semantic_score'] = float(similarities[idx])
            candidate['heuristic_bonus'] = 0.0
            candidate['final_score'] = float(similarities[idx])
            ranked_candidates.append(candidate)
        
        return ranked_candidates
    
    def get_similarities(self, query_embedding: np.ndarray, signature_embeddings: np.ndarray) -> np.ndarray:
        """
        Get all similarity scores for debugging
        
        Args:
            query_embedding: Query vector
            signature_embeddings: Matrix of signature vectors
            
        Returns:
            Array of all similarity scores
        """
        return self._calculate_similarities(query_embedding, signature_embeddings) 