from pydantic import BaseModel
from typing import Optional

class ResolveLocatorRequest(BaseModel):
    description: str
    dom: str
    screenshot_b64: Optional[str] = None

class ResolveLocatorResponse(BaseModel):
    locator: str

class LocatorResolveRequest(BaseModel):
    description: str
    dom: str
    screenshot_path: str

class LocatorResolveResponse(BaseModel):
    locator: str 