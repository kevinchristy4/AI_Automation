from pydantic import BaseModel
from typing import Optional

class ExecuteRequest(BaseModel):
    action: str
    locator: str
    value: Optional[str] = None

class ExecuteResponse(BaseModel):
    success: bool
    message: Optional[str] = None 