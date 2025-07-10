import re
from typing import List, Dict, Any
from .vector_ranker import RankingStrategy

class HeuristicRanker(RankingStrategy):
    """
    Handles heuristic re-ranking based on actionability and user intent.
    Extracted from TwoStageLocatorResolver logic for better separation of concerns.
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
    
    def __init__(self):
        self.debug = False
    
    def set_debug(self, debug: bool):
        """Enable or disable debug output"""
        self.debug = debug
    
    def rank(self, candidates: List[Dict], context: Dict) -> List[Dict]:
        """
        Re-rank candidates based on actionability heuristics
        
        Args:
            candidates: List of candidates from previous ranking stage
            context: Dictionary containing 'user_step' and optionally 'action_type'
            
        Returns:
            Re-ranked list of candidates with final scores
        """
        user_step = context.get('user_step', '')
        action_type = context.get('action_type')
        
        if not action_type:
            action_type = self._detect_action_type(user_step)
        
        if self.debug:
            print(f"HeuristicRanker: Detected Action Type: {action_type}")
        
        # Calculate heuristic bonus for each candidate
        for candidate in candidates:
            heuristic_bonus = self._calculate_heuristic_bonus(candidate, action_type, user_step)
            candidate['heuristic_bonus'] = heuristic_bonus
            candidate['final_score'] = candidate['semantic_score'] + heuristic_bonus
        
        # Sort by final score (descending)
        ranked_candidates = sorted(candidates, key=lambda x: x['final_score'], reverse=True)
        
        if self.debug:
            print(f"HeuristicRanker: Re-ranked {len(ranked_candidates)} candidates by actionability")
            for i, candidate in enumerate(ranked_candidates[:3]):
                print(f"  {i+1}. Final: {candidate['final_score']:.3f} | Semantic: {candidate['semantic_score']:.3f} | Heuristic: {candidate['heuristic_bonus']:.3f}")
                print(f"      {candidate['signature'][:50]}...")
        
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