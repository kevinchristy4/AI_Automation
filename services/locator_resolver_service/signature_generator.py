class SignatureGenerator:
    """
    Generates semantic signatures for DOM elements.
    Returns None for elements with no meaningful content (just tag name).
    """
    
    @staticmethod
    def generate_signature(element):
        """
        Generate a semantic signature for a DOM element.
        Returns None if the element has no meaningful content (just tag name).
        """
        tag = element.name
        text = ""
        for content in element.contents:
            if isinstance(content, str):
                text += content.strip() + " "
        text = text.strip()
        
        parts = []
        
        # Always start with the tag name
        if tag:
            if text:
                parts.append(f"{tag}: {text}")
            else:
                parts.append(tag)
        elif text:
            parts.append(text)

        # Add key attributes
        key_attrs = [
            "aria-label", "aria-labelledby", "id", "name", "placeholder", 
            "alt", "title", "value", "type", "role", "href", "class"
        ]
        for attr in key_attrs:
            val = element.attrs.get(attr)
            if isinstance(val, list):
                val = " ".join(str(v) for v in val)
            if val:
                parts.append(f"{attr}: {val}")
        
        signature = ", ".join(parts)
        
        # Return None if signature is just the tag name (no meaningful content)
        if signature == tag:
            return None
            
        return signature 