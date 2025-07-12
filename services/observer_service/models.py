from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class NavigateRequest(BaseModel):
    url: str

class NavigateResponse(BaseModel):
    success: bool
    message: Optional[str] = None

class StateResponse(BaseModel):
    dom: str
    screenshot_path: str

class AccessibilityTreeResponse(BaseModel):
    success: bool
    accessibility_tree: Optional[Dict[str, Any]] = None
    message: Optional[str] = None

class ActionRequest(BaseModel):
    action: str
    locator: Optional[str] = None
    value: Optional[str] = None
    url: Optional[str] = None

class ActionResponse(BaseModel):
    success: bool
    message: Optional[str] = None 