import re
from typing import List, Dict, Tuple, Optional
from .vectordb import VectorDatabase
from .embedding import EmbeddingModel

class TwoStageLocatorResolver:
    """
    Two-stage locator resolver that combines semantic search with heuristic re-ranking
    to solve the semantic vs. actionability problem.
    
    Stage 1: Semantic Search - Find top-K candidates using vector similarity
    Stage 2: Heuristic Re-ranking - Re-rank candidates based on actionability and intent
    """
    
    # Action keywords and their associated element types
    ACTION_KEYWORDS = {
        'click': {
            'keywords': ['click', 'press', 'tap', 'submit', 'button'],
            'priority_elements': ['button', 'a', 'input[type="submit"]', 'input[type="button"]'],
            'priority_roles': ['button', 'link', 'menuitem', 'tab'],
            'bonus_score': 0.5
        },
        'input': {
            'keywords': ['enter', 'type', 'fill', 'input', 'write'],
            'priority_elements': ['input', 'textarea'],
            'priority_roles': ['textbox', 'searchbox'],
            'bonus_score': 0.5
        },
        'select': {
            'keywords': ['select', 'choose', 'pick', 'dropdown'],
            'priority_elements': ['select', 'option'],
            'priority_roles': ['listbox', 'option'],
            'bonus_score': 0.5
        },
        'verify': {
            'keywords': ['find', 'see', 'look', 'check', 'verify', 'confirm'],
            'priority_elements': ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'span', 'div'],
            'priority_roles': ['heading', 'text'],
            'bonus_score': 0.2
        }
    }
    
    def __init__(self, vector_db: VectorDatabase, embedding_model: EmbeddingModel):
        self.vector_db = vector_db
        self.embedding_model = embedding_model
        self.debug = False
    
    def set_debug(self, debug: bool):
        """Enable or disable debug output"""
        self.debug = debug
    
    def resolve_locator(self, user_step: str, top_k: int = 10) -> List[Dict]:
        """
        Main method to resolve locator using two-stage approach
        
        Args:
            user_step: The user's command (e.g., "Click the Sign In button")
            top_k: Number of candidates to retrieve in Stage 1
            
        Returns:
            List of ranked candidates with scores and locators
        """
        if self.debug:
            print(f"\n=== Two-Stage Locator Resolution ===")
            print(f"User Step: {user_step}")
        
        # Stage 1: Semantic Search
        candidates = self._stage1_semantic_search(user_step, top_k)
        
        if self.debug:
            print(f"\nStage 1 Results ({len(candidates)} candidates):")
            for i, candidate in enumerate(candidates[:5]):  # Show top 5
                print(f"  {i+1}. Score: {candidate['semantic_score']:.3f} | Signature: {candidate['signature'][:100]}...")
            
            # Show all candidates if debug is enabled
            print(f"\nAll Stage 1 Candidates:")
            for i, candidate in enumerate(candidates):
                print(f"  {i+1}. Score: {candidate['semantic_score']:.3f} | Signature: {candidate['signature']}")
        
        # Stage 2: Heuristic Re-ranking
        ranked_candidates = self._stage2_heuristic_rerank(user_step, candidates)
        
        if self.debug:
            print(f"\nStage 2 Final Results:")
            for i, candidate in enumerate(ranked_candidates[:5]):  # Show top 5
                print(f"  {i+1}. Final Score: {candidate['final_score']:.3f} | Semantic: {candidate['semantic_score']:.3f} | Heuristic: {candidate['heuristic_bonus']:.3f}")
                print(f"      Signature: {candidate['signature'][:100]}...")
        
        return ranked_candidates
    
    def _stage1_semantic_search(self, user_step: str, top_k: int) -> List[Dict]:
        """
        Stage 1: Semantic search using vector similarity
        
        Args:
            user_step: User's command
            top_k: Number of candidates to retrieve
            
        Returns:
            List of candidates with semantic scores
        """
        # Embed the user step
        query_embedding = self.embedding_model.embed([user_step])
        
        # Get all similarities
        similarities = self.vector_db.get_similarities(query_embedding)
        
        # Get top-k indices
        top_indices = similarities.argsort()[-top_k:][::-1]
        
        # Convert to candidate format
        candidates = []
        for idx in top_indices:
            element = self.vector_db.elements[idx]
            similarity_score = similarities[idx]
            candidates.append({
                'element': element,
                'signature': element.get('signature', ''),
                'locators': element.get('locators', []),
                'semantic_score': float(similarity_score),
                'heuristic_bonus': 0.0,
                'final_score': float(similarity_score)
            })
        
        return candidates
    
    def _stage2_heuristic_rerank(self, user_step: str, candidates: List[Dict]) -> List[Dict]:
        """
        Stage 2: Heuristic re-ranking based on actionability
        
        Args:
            user_step: User's command
            candidates: List of candidates from Stage 1
            
        Returns:
            Re-ranked list of candidates with final scores
        """
        # Detect action type from user step
        action_type = self._detect_action_type(user_step)
        
        if self.debug:
            print(f"\nDetected Action Type: {action_type}")
        
        # Calculate heuristic bonus for each candidate
        for candidate in candidates:
            heuristic_bonus = self._calculate_heuristic_bonus(candidate, action_type, user_step)
            candidate['heuristic_bonus'] = heuristic_bonus
            candidate['final_score'] = candidate['semantic_score'] + heuristic_bonus
        
        # Sort by final score (descending)
        ranked_candidates = sorted(candidates, key=lambda x: x['final_score'], reverse=True)
        
        return ranked_candidates
    
    def _detect_action_type(self, user_step: str) -> str:
        """
        Detect the primary action type from the user step
        
        Args:
            user_step: User's command
            
        Returns:
            Action type ('click', 'input', 'select', 'verify', or 'unknown')
        """
        user_step_lower = user_step.lower()
        
        # Count keyword matches for each action type
        action_scores = {}
        for action_type, config in self.ACTION_KEYWORDS.items():
            score = 0
            for keyword in config['keywords']:
                if keyword in user_step_lower:
                    score += 1
            action_scores[action_type] = score
        
        # Find the action type with the highest score
        if action_scores:
            best_action = max(action_scores.items(), key=lambda x: x[1])
            if best_action[1] > 0:
                return best_action[0]
        
        return 'unknown'
    
    def _calculate_heuristic_bonus(self, candidate: Dict, action_type: str, user_step: str) -> float:
        """
        Calculate heuristic bonus score for a candidate based on actionability.
        Corrected version to robustly handle different signature formats and apply bonuses accurately.
        """
        if action_type == 'unknown':
            return 0.0

        action_config = self.ACTION_KEYWORDS.get(action_type, {})
        if not action_config:
            return 0.0

        bonus_score = 0.0
        base_bonus = action_config.get('bonus_score', 0.0)
        signature = candidate.get('signature', '').lower()
        locators = candidate.get('locators', [])
        user_step_lower = user_step.lower()

        if self.debug:
            print(f"    Calculating bonus for: {candidate['signature'][:60]}...")

        # --- Corrected Tag and Role Extraction ---
        element_tag_match = re.match(r'^([a-zA-Z0-9]+)[\s,:]', signature)
        element_tag = element_tag_match.group(1) if element_tag_match else ""
        
        element_role = ""
        for loc in locators:
            if loc.get('type') == 'get_by_role':
                match = re.search(r"get_by_role\('([^']*)'", loc.get('locator', ''))
                if match:
                    element_role = match.group(1)
                    break
        # --- End Correction ---

        # 1. Priority Bonus (based on action type)
        priority_elements = action_config.get('priority_elements', [])
        priority_roles = action_config.get('priority_roles', [])

        is_priority = False
        if element_tag in priority_elements or element_role in priority_roles:
            is_priority = True
        else:
            for pe in priority_elements:
                if '[' in pe and pe in signature:
                    is_priority = True
                    break
        
        if is_priority:
            bonus_score += base_bonus
            if self.debug:
                print(f"      +{base_bonus:.2f} for priority element/role: tag='{element_tag}', role='{element_role}'")

        # 2. Explicit Mention Bonuses
        if action_type == 'click':
            if 'button' in user_step_lower:
                if element_tag == 'button' or element_role == 'button':
                    bonus_score += base_bonus * 1.5
                    if self.debug:
                        print(f"      +{base_bonus * 1.5:.2f} for explicit 'button' mention on a button")
                elif element_tag == 'a' or element_role == 'link':
                    bonus_score += base_bonus * 1.2
                    if self.debug:
                        print(f"      +{base_bonus * 1.2:.2f} for 'button' mention on a link")
            if 'link' in user_step_lower:
                 if element_tag == 'a' or element_role == 'link':
                    bonus_score += base_bonus * 1.5
                    if self.debug:
                        print(f"      +{base_bonus * 1.5:.2f} for explicit 'link' mention on a link")

        if action_type == 'input' and any(word in user_step_lower for word in ['field', 'input', 'text']):
            if element_tag in ['input', 'textarea'] or element_role in ['textbox', 'searchbox']:
                bonus_score += base_bonus * 1.2
                if self.debug:
                    print(f"      +{base_bonus * 1.2:.2f} for input keyword on an input field")

        # 3. Word Overlap Bonus
        user_words = set(re.findall(r'\b\w+\b', user_step_lower))
        signature_words = set(re.findall(r'\b\w+\b', signature))
        common_words = user_words.intersection(signature_words)
        
        if len(common_words) > 0:
            word_overlap_bonus = len(common_words) / len(user_words) * 0.1
            bonus_score += word_overlap_bonus
            if self.debug:
                print(f"      +{word_overlap_bonus:.3f} for word overlap: {common_words}")
        
        if self.debug:
            print(f"      Total bonus: {bonus_score:.3f}")
        
        return min(bonus_score, 1.0)  # Cap bonus at 1.0 