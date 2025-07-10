from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class LocatorRequest(BaseModel):
    dom: List[Dict[str, Any]]  # Simplified DOM: [{"signature": str, "locators": List[Dict]}]
    user_step: str
    debug: Optional[bool] = False

class LocatorResponse(BaseModel):
    best_locator: Optional[Dict[str, Any]]
    best_element: Dict[str, Any]  # Contains signature and locators
    similarity: float 