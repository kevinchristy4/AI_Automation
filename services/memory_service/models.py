from pydantic import BaseModel
from typing import Any, Optional

class GetRequest(BaseModel):
    key: str

class GetResponse(BaseModel):
    value: Optional[Any] = None

class SetRequest(BaseModel):
    key: str
    value: Any

class SetResponse(BaseModel):
    success: bool
    message: Optional[str] = None

class AppendLogRequest(BaseModel):
    log_entry: str

class AppendLogResponse(BaseModel):
    success: bool
    message: Optional[str] = None 