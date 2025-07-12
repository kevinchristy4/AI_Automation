import re
from typing import List, Dict, Any, Optional
from .accessibility_scorer import AccessibilityLocatorScorer

class AccessibilityLocatorGenerator:
    """
    Generates Playwright locators from accessibility tree data.
    Similar to DomParser.generate_locators but adapted for accessibility tree structure.
    """
    
    # Roles that support get_by_role locators
    SUPPORTED_ROLES = {
        'button', 'link', 'heading', 'checkbox', 'radio', 'textbox', 'listitem', 
        'menu', 'menuitem', 'tab', 'tabpanel', 'dialog', 'list', 'listbox', 
        'option', 'combobox', 'searchbox', 'spinbutton', 'slider', 'switch',
        'tree', 'treeitem', 'grid', 'gridcell', 'row', 'columnheader', 'rowheader',
        'text', 'generic', 'banner', 'main', 'navigation', 'contentinfo', 'article',
        'section', 'aside', 'form', 'search', 'region', 'complementary', 'application'
    }
    
    # Interactive roles that are typically actionable
    INTERACTIVE_ROLES = {
        'button', 'link', 'checkbox', 'radio', 'textbox', 'menuitem', 'tab',
        'option', 'combobox', 'searchbox', 'spinbutton', 'slider', 'switch',
        'treeitem', 'gridcell'
    }
    
    @staticmethod
    def generate_locators_from_accessibility_tree(accessibility_tree: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate locators for all elements in the accessibility tree.
        
        Args:
            accessibility_tree: The accessibility tree dictionary
            
        Returns:
            List of dictionaries with signature and locators for each element
        """
        elements = []
        
        def process_node(node: Dict[str, Any]):
            if not node:
                return
                
            # Generate locators for this node
            locators = AccessibilityLocatorGenerator._generate_node_locators(node)
            
            if locators:  # Only add elements that have meaningful locators
                # Generate signature for this node
                signature = AccessibilityLocatorGenerator._generate_signature(node)
                
                if signature:
                    elements.append({
                        "signature": signature,
                        "locators": sorted(locators, key=lambda x: x["score"], reverse=True)
                    })
                else:
                    # Debug: Log why signature was rejected
                    role = node.get('role', '')
                    name = node.get('name', '')
                    print(f"DEBUG: Signature rejected for role='{role}', name='{name}'")
            else:
                # Debug: Log why locators were rejected
                role = node.get('role', '')
                name = node.get('name', '')
                disabled = node.get('disabled', False)
                print(f"DEBUG: No locators generated for role='{role}', name='{name}', disabled={disabled}")
            
            # Process children recursively
            children = node.get('children', [])
            for child in children:
                process_node(child)
        
        process_node(accessibility_tree)
        return elements
    
    @staticmethod
    def _generate_node_locators(node: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate locators for a single accessibility tree node.
        """
        locators = []
        
        role = node.get('role', '')
        name = node.get('name', '')
        value = node.get('value', '')
        description = node.get('description', '')
        level = node.get('level')
        disabled = node.get('disabled', False)
        required = node.get('required', False)
        expanded = node.get('expanded')
        selected = node.get('selected')
        
        # Skip disabled elements unless specifically needed
        if disabled:
            return []
        
        # 1. Generate get_by_role locator (highest priority for semantic roles)
        if role in AccessibilityLocatorGenerator.SUPPORTED_ROLES:
            # Build locator options dynamically
            locator_options = {}
            
            # Add name if available
            if name:
                locator_options['name'] = name
            
            # Add additional options for specific roles
            if role == 'heading' and level:
                locator_options['level'] = level
            if role == 'textbox' and value:
                locator_options['value'] = value
            if role in ['checkbox', 'radio'] and selected is not None:
                locator_options['checked'] = selected
            if role == 'combobox' and expanded is not None:
                locator_options['expanded'] = expanded
            if required:
                locator_options['required'] = True
            
            # Generate the locator string
            if locator_options:
                # Convert options to string format
                options_str = ', '.join([
                    f'{k}: "{v}"' if isinstance(v, str) else f'{k}: {str(v).lower()}' 
                    for k, v in locator_options.items()
                ])
                locator_string = f'page.get_by_role("{role}", {{ {options_str} }})'
            else:
                # Role-only locator
                locator_string = f'page.get_by_role("{role}")'
            
            score = AccessibilityLocatorScorer.score_locator("get_by_role", locator_string, node)
            locators.append({"type": "get_by_role", "locator": locator_string, "score": score})
        
        # 2. Generate get_by_text locator for elements with names (always generate if name exists)
        if name and len(name.strip()) > 0:
            # Clean the text (remove extra whitespace)
            clean_name = re.sub(r'\s+', ' ', name.strip())
            exact = ", { exact: true }" if len(clean_name) < 30 else ""
            locator_string = f'page.get_by_text("{clean_name}"{exact})'
            score = AccessibilityLocatorScorer.score_locator("get_by_text", locator_string, node)
            locators.append({"type": "get_by_text", "locator": locator_string, "score": score})
        
        # 3. Generate get_by_label locator for form elements
        if role in ['textbox', 'checkbox', 'radio', 'combobox', 'listbox', 'spinbutton', 'slider'] and name:
            locator_string = f'page.get_by_label("{name}")'
            score = AccessibilityLocatorScorer.score_locator("get_by_label", locator_string, node)
            locators.append({"type": "get_by_label", "locator": locator_string, "score": score})
        
        # 4. Generate get_by_placeholder locator for text inputs
        if role == 'textbox' and description:
            locator_string = f'page.get_by_placeholder("{description}")'
            score = AccessibilityLocatorScorer.score_locator("get_by_placeholder", locator_string, node)
            locators.append({"type": "get_by_placeholder", "locator": locator_string, "score": score})
        
        # 5. Generate accessibility-based XPath locator
        # Create an accessibility-based XPath
        axpath = AccessibilityLocatorGenerator._generate_accessibility_xpath(node)
        if axpath:
            locator_string = f'page.locator("{axpath}")'
            score = AccessibilityLocatorScorer.score_locator("xpath", locator_string, node)
            locators.append({"type": "xpath", "locator": locator_string, "score": score})
        
        # 6. Generate get_by_test_id if available (common in modern apps)
        if 'testid' in node or 'data-testid' in node:
            test_id = node.get('testid') or node.get('data-testid')
            if test_id:
                locator_string = f'page.get_by_test_id("{test_id}")'
                score = AccessibilityLocatorScorer.score_locator("test_id", locator_string, node)
                locators.append({"type": "test_id", "locator": locator_string, "score": score})
        
        return locators
    
    @staticmethod
    def _generate_signature(node: Dict[str, Any]) -> Optional[str]:
        """
        Generate a semantic signature for an accessibility tree node.
        """
        parts = []
        
        role = node.get('role', '')
        name = node.get('name', '')
        value = node.get('value', '')
        level = node.get('level')
        
        # Start with role
        if role:
            if level and role == 'heading':
                parts.append(f"{role} (level {level})")
            else:
                parts.append(role)
        
        # Add name if available
        if name:
            parts.append(f"name: {name}")
        
        # Add value for form controls
        if value and role in ['textbox', 'combobox', 'listbox', 'spinbutton', 'slider']:
            parts.append(f"value: {value}")
        
        # Add additional properties
        if node.get('disabled'):
            parts.append("disabled")
        if node.get('required'):
            parts.append("required")
        if node.get('selected') is not None:
            parts.append(f"selected: {node.get('selected')}")
        if node.get('expanded') is not None:
            parts.append(f"expanded: {node.get('expanded')}")
        
        signature = ", ".join(parts)
        
        # Return None only if there's no meaningful content at all
        # Allow elements with names even if they have generic roles
        if not name and not value and signature == role:
            return None
            
        return signature
    
    @staticmethod
    def _generate_accessibility_xpath(node: Dict[str, Any]) -> Optional[str]:
        """
        Generate an accessibility-based XPath for the node.
        This creates XPaths that work with real-world HTML structures.
        """
        name = node.get('name', '')
        role = node.get('role', '')
        level = node.get('level')
        
        if not name:
            return None
        
        # Escape single quotes in the name for XPath
        escaped_name = name.replace("'", "\\'")
        
        # Build accessibility-based XPath focusing on content matching
        xpath_parts = []
        
        # Start with any element that contains the name
        xpath_parts.append("//*[")
        
        # Primary condition: match by aria-label or text content
        xpath_parts.append(f"contains(@aria-label, '{escaped_name}') or contains(text(), '{escaped_name}')")
        
        # For headings, add additional matching strategies
        if role == 'heading' and level:
            # Try multiple heading detection strategies
            xpath_parts.append(f" or (self::h{level} and contains(text(), '{escaped_name}'))")
            xpath_parts.append(f" or (contains(@class, 'heading') and contains(text(), '{escaped_name}'))")
            xpath_parts.append(f" or (contains(@class, 'title') and contains(text(), '{escaped_name}'))")
            xpath_parts.append(f" or (@aria-level='{level}' and contains(text(), '{escaped_name}'))")
        
        # For buttons, add button-specific matching
        elif role == 'button':
            xpath_parts.append(f" or (self::button and contains(text(), '{escaped_name}'))")
            xpath_parts.append(f" or (contains(@class, 'btn') and contains(text(), '{escaped_name}'))")
            xpath_parts.append(f" or (contains(@class, 'button') and contains(text(), '{escaped_name}'))")
            xpath_parts.append(f" or (contains(@class, 'submit') and contains(text(), '{escaped_name}'))")
        
        # For links, add link-specific matching
        elif role == 'link':
            xpath_parts.append(f" or (self::a and contains(text(), '{escaped_name}'))")
            xpath_parts.append(f" or (contains(@class, 'link') and contains(text(), '{escaped_name}'))")
            xpath_parts.append(f" or (contains(@class, 'nav-link') and contains(text(), '{escaped_name}'))")
        
        # For form elements, add form-specific matching
        elif role in ['textbox', 'combobox', 'listbox']:
            xpath_parts.append(f" or (self::input and contains(@placeholder, '{escaped_name}'))")
            xpath_parts.append(f" or (self::input and contains(@name, '{escaped_name}'))")
            xpath_parts.append(f" or (self::input and contains(@id, '{escaped_name}'))")
            xpath_parts.append(f" or (self::textarea and contains(@placeholder, '{escaped_name}'))")
        
        # For checkboxes and radio buttons
        elif role in ['checkbox', 'radio']:
            xpath_parts.append(f" or (self::input[@type='{role}'] and contains(@name, '{escaped_name}'))")
            xpath_parts.append(f" or (self::input[@type='{role}'] and contains(@id, '{escaped_name}'))")
        
        # Close the primary condition
        xpath_parts.append("]")
        
        # Add state-based filters if applicable
        additional_filters = []
        
        if node.get('disabled'):
            additional_filters.append("@disabled='disabled' or @aria-disabled='true'")
        
        if node.get('required'):
            additional_filters.append("@required='required' or @aria-required='true'")
        
        if node.get('selected') is not None:
            checked_value = str(node.get('selected')).lower()
            additional_filters.append(f"@checked='checked' or @aria-checked='{checked_value}'")
        
        if node.get('expanded') is not None:
            expanded_value = str(node.get('expanded')).lower()
            additional_filters.append(f"@aria-expanded='{expanded_value}'")
        
        # If we have additional filters, create a more specific XPath with proper grouping
        if additional_filters:
            # Create a new XPath with state filters properly grouped
            # The element must match both the name/text condition AND the state condition
            name_conditions = f"contains(@aria-label, '{escaped_name}') or contains(text(), '{escaped_name}')"
            
            # Add role-specific name conditions
            if role == 'heading' and level:
                name_conditions += f" or (self::h{level} and contains(text(), '{escaped_name}'))"
                name_conditions += f" or (contains(@class, 'heading') and contains(text(), '{escaped_name}'))"
                name_conditions += f" or (contains(@class, 'title') and contains(text(), '{escaped_name}'))"
                name_conditions += f" or (@aria-level='{level}' and contains(text(), '{escaped_name}'))"
            elif role == 'button':
                name_conditions += f" or (self::button and contains(text(), '{escaped_name}'))"
                name_conditions += f" or (contains(@class, 'btn') and contains(text(), '{escaped_name}'))"
                name_conditions += f" or (contains(@class, 'button') and contains(text(), '{escaped_name}'))"
                name_conditions += f" or (contains(@class, 'submit') and contains(text(), '{escaped_name}'))"
            elif role == 'link':
                name_conditions += f" or (self::a and contains(text(), '{escaped_name}'))"
                name_conditions += f" or (contains(@class, 'link') and contains(text(), '{escaped_name}'))"
                name_conditions += f" or (contains(@class, 'nav-link') and contains(text(), '{escaped_name}'))"
            elif role in ['textbox', 'combobox', 'listbox']:
                name_conditions += f" or (self::input and contains(@placeholder, '{escaped_name}'))"
                name_conditions += f" or (self::input and contains(@name, '{escaped_name}'))"
                name_conditions += f" or (self::input and contains(@id, '{escaped_name}'))"
                name_conditions += f" or (self::textarea and contains(@placeholder, '{escaped_name}'))"
            elif role in ['checkbox', 'radio']:
                name_conditions += f" or (self::input[@type='{role}'] and contains(@name, '{escaped_name}'))"
                name_conditions += f" or (self::input[@type='{role}'] and contains(@id, '{escaped_name}'))"
            
            state_conditions = ' or '.join(additional_filters)
            state_xpath = f"//*[({name_conditions}) and ({state_conditions})]"
            return state_xpath
        
        # Return the basic XPath
        return "".join(xpath_parts) 