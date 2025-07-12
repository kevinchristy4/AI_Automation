from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# DOM-based resolver models
class DomBasedLocatorRequest(BaseModel):
    description: str
    dom: str
    screenshot_path: str

class DomBasedLocatorResponse(BaseModel):
    locator: str

# Accessibility-based resolver models
class AccessibilityLocatorRequest(BaseModel):
    accessibility_tree: Dict[str, Any]
    include_ignored: Optional[bool] = False
    include_hidden: Optional[bool] = False

class AccessibilityLocatorResponse(BaseModel):
    success: bool
    elements: Optional[List[Dict[str, Any]]] = None
    message: Optional[str] = None 