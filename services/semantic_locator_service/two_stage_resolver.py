import re
import numpy as np
from typing import List, Dict, Tuple, Optional
from .vectordb import VectorDatabase
from .embedding import EmbeddingModel
from .vector_ranker import VectorRanker
from .heuristic_ranker import HeuristicRanker

class TwoStageLocatorResolver:
    """
    Two-stage locator resolver that orchestrates vector similarity search and heuristic re-ranking
    to solve the semantic vs. actionability problem.
    
    Stage 1: Semantic Search - Find top-K candidates using vector similarity
    Stage 2: Heuristic Re-ranking - Re-rank candidates based on actionability and intent
    """
    
    def __init__(self, vector_db: VectorDatabase, embedding_model: EmbeddingModel):
        self.vector_db = vector_db
        self.embedding_model = embedding_model
        self.vector_ranker = VectorRanker(embedding_model)
        self.heuristic_ranker = HeuristicRanker()
        self.debug = False
    
    def set_debug(self, debug: bool):
        """Enable or disable debug output"""
        self.debug = debug
        self.vector_ranker.set_debug(debug)
        self.heuristic_ranker.set_debug(debug)
    
    def _distill_query(self, user_step: str) -> str:
        """
        Distills the user step down to its core semantic meaning by removing action
        and element type keywords.
        e.g., "Click the 'Login' button" -> "Login"
        """
        distilled_query = user_step
        
        # Prioritize quoted text as the core semantic meaning. Use a robust regex.
        quoted_text = re.findall(r'([^\"]*)\'|\"([^\"]*)\"', distilled_query)
        if quoted_text:
            # Join all non-empty captured groups from all matches
            distilled_query = " ".join(filter(None, [item for sublist in quoted_text for item in sublist]))
        else:
            # If no quotes, remove action, element type, and stop words
            all_keywords = set()
            for action_config in HeuristicRanker.ACTION_KEYWORDS.values():
                all_keywords.update(action_config['keywords'])
                # Handle complex selectors like 'input[type="submit"]' -> 'input'
                all_keywords.update([e.split('[')[0] for e in action_config['priority_elements']])
                all_keywords.update(action_config['priority_roles'])

            # Add common English stop words
            all_keywords.update(['the', 'a', 'an', 'in', 'on', 'of', 'to', 'for', 'is', 'are', 'was', 'were'])

            # Remove keywords from the query, preserving order
            words = re.findall(r'\b\w+\b', distilled_query)
            distilled_words = [word for word in words if word.lower() not in all_keywords]
            distilled_query = " ".join(distilled_words)

        # If distillation results in an empty string, fall back to the original query
        if not distilled_query.strip():
            if self.debug:
                print(f"Query distillation resulted in an empty string. Falling back to original user step.")
            return user_step

        if self.debug:
            print(f"Distilled Query for Stage 1: '{distilled_query}'")
            
        return distilled_query

    def resolve_locator(self, user_step: str, top_k: int = 10) -> List[Dict]:
        """
        Main method to resolve locator using two-stage approach.
        It now uses a distilled query for Stage 1 and the original query for Stage 2.
        """
        if self.debug:
            print(f"\n=== Two-Stage Locator Resolution ===")
            print(f"User Step: {user_step}")
        
        # Distill the query for a more focused semantic search in Stage 1
        distilled_query = self._distill_query(user_step)

        # Stage 1: Vector Similarity Ranking using the distilled query
        candidates = self._stage1_vector_ranking(distilled_query, top_k)
        
        if self.debug:
            print(f"\nStage 1 Results ({len(candidates)} candidates found using '{distilled_query}'):")
            for i, candidate in enumerate(candidates[:5]):  # Show top 5
                print(f"  {i+1}. Score: {candidate['semantic_score']:.3f} | Signature: {candidate['signature'][:100]}...")
            
            if len(candidates) > 5:
                print(f"\nAll Stage 1 Candidates:")
                for i, candidate in enumerate(candidates):
                    print(f"  {i+1}. Score: {candidate['semantic_score']:.3f} | Signature: {candidate['signature']}")
        
        # Stage 2: Heuristic Re-ranking using the original, full user step
        ranked_candidates = self._stage2_heuristic_ranking(user_step, candidates)
        
        if self.debug:
            print(f"\nStage 2 Final Results:")
            for i, candidate in enumerate(ranked_candidates[:5]):  # Show top 5
                print(f"  {i+1}. Final Score: {candidate['final_score']:.3f} | Semantic: {candidate['semantic_score']:.3f} | Heuristic: {candidate['heuristic_bonus']:.3f}")
                print(f"      Signature: {candidate['signature'][:100]}...")
        
        return ranked_candidates
    
    def _stage1_vector_ranking(self, query: str, top_k: int) -> List[Dict]:
        """
        Stage 1: Vector similarity ranking using the VectorRanker
        
        Args:
            query: The distilled user command
            top_k: Number of candidates to retrieve
            
        Returns:
            List of candidates with semantic scores
        """
        # Embed the distilled query
        query_embedding = self.embedding_model.embed([query])
        
        # Use VectorRanker to rank candidates
        candidates = self.vector_ranker.rank(self.vector_db.elements, query_embedding)
        
        # Limit to top_k if needed
        if len(candidates) > top_k:
            candidates = candidates[:top_k]
        
        return candidates
    
    def _stage2_heuristic_ranking(self, user_step: str, candidates: List[Dict]) -> List[Dict]:
        """
        Stage 2: Heuristic re-ranking using the HeuristicRanker
        
        Args:
            user_step: Original user command
            candidates: List of candidates from Stage 1
            
        Returns:
            Re-ranked list of candidates with final scores
        """
        # Prepare context for HeuristicRanker
        context = {
            'user_step': user_step
        }
        
        # Use HeuristicRanker to re-rank candidates
        ranked_candidates = self.heuristic_ranker.rank(candidates, context)
        
        return ranked_candidates 