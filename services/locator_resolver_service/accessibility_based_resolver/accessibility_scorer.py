import re
from typing import Dict, Any

class AccessibilityLocatorScorer:
    """
    Scores locators generated from accessibility tree data.
    Similar to LocatorScorer but adapted for accessibility properties.
    """
    
    BASE_SCORES = {
        "get_by_role": 0.95,  # Highest priority for accessibility-based locators
        "get_by_label": 0.90,
        "get_by_text": 0.80,
        "get_by_placeholder": 0.85,
        "test_id": 0.88,
        "xpath": 0.60,  # Lower priority for accessibility-based XPath
    }
    
    # Interactive roles get bonus points
    INTERACTIVE_ROLE_BONUS = 0.05
    
    # Roles that are typically actionable
    INTERACTIVE_ROLES = {
        'button', 'link', 'checkbox', 'radio', 'textbox', 'menuitem', 'tab',
        'option', 'combobox', 'searchbox', 'spinbutton', 'slider', 'switch',
        'treeitem', 'gridcell'
    }
    
    @staticmethod
    def score_locator(locator_type: str, locator_string: str, node: Dict[str, Any]) -> float:
        """
        Score a locator based on accessibility properties.
        
        Args:
            locator_type: Type of locator (get_by_role, get_by_text, etc.)
            locator_string: The actual locator string
            node: The accessibility tree node
            
        Returns:
            Score between 0 and 1
        """
        score = AccessibilityLocatorScorer.BASE_SCORES.get(locator_type, 0.0)
        
        role = node.get('role', '')
        name = node.get('name', '')
        value = node.get('value', '')
        required = node.get('required', False)
        
        # Bonus for interactive roles
        if role in AccessibilityLocatorScorer.INTERACTIVE_ROLES:
            score += AccessibilityLocatorScorer.INTERACTIVE_ROLE_BONUS
        
        # Score based on name quality
        if name:
            word_count = len(name.split())
            if 1 <= word_count <= 5:
                score += 0.05  # Good length
            elif word_count > 10:
                score -= 0.05  # Too verbose
            
            # Bonus for meaningful names (not just generic text)
            if not AccessibilityLocatorScorer._is_generic_text(name):
                score += 0.03
        else:
            # Penalty for elements without names (except for role-only locators)
            if locator_type != "get_by_role" or role not in AccessibilityLocatorScorer.INTERACTIVE_ROLES:
                score -= 0.1
        
        # Bonus for form elements with values
        if value and role in ['textbox', 'combobox', 'listbox', 'spinbutton', 'slider']:
            score += 0.02
        
        # Bonus for required form elements
        if required:
            score += 0.02
        
        # Penalty for very generic roles without specific identifiers
        if role in ['generic', 'text'] and not name:
            score -= 0.15
        
        # Bonus for specific role types that are commonly used
        if role in ['button', 'link', 'heading']:
            score += 0.02
        
        # Penalty for overly complex locators
        if len(locator_string) > 200:
            score -= 0.05
        
        # Special handling for role-only locators
        if locator_type == "get_by_role" and not name:
            # Only penalize if it's not an interactive role
            if role not in AccessibilityLocatorScorer.INTERACTIVE_ROLES:
                score -= 0.1
        
        # Ensure score is within bounds
        return round(max(0.0, min(1.0, score)), 2)
    
    @staticmethod
    def _is_generic_text(text: str) -> bool:
        """
        Check if text is generic and not very descriptive.
        """
        if not text:
            return True
        
        # Common generic texts
        generic_texts = {
            'click', 'submit', 'ok', 'cancel', 'yes', 'no', 'next', 'previous',
            'back', 'forward', 'close', 'open', 'save', 'delete', 'edit',
            'add', 'remove', 'search', 'filter', 'sort', 'refresh', 'reload',
            'loading', 'error', 'success', 'warning', 'info', 'help'
        }
        
        text_lower = text.lower().strip()
        
        # Check if it's a single generic word
        if text_lower in generic_texts:
            return True
        
        # Check if it's very short (1-2 characters)
        if len(text_lower) <= 2:
            return True
        
        # Check if it's mostly numbers or special characters
        if not any(c.isalpha() for c in text_lower):
            return True
        
        return False 