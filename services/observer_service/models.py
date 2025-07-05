from pydantic import BaseModel
from typing import Optional

class NavigateRequest(BaseModel):
    url: str

class NavigateResponse(BaseModel):
    success: bool
    message: Optional[str] = None

class StateResponse(BaseModel):
    dom: str
    screenshot_path: str

class ActionRequest(BaseModel):
    action: str
    locator: Optional[str] = None
    value: Optional[str] = None
    url: Optional[str] = None

class ActionResponse(BaseModel):
    success: bool
    message: Optional[str] = None 