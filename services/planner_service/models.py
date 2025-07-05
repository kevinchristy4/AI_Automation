from pydantic import BaseModel
from typing import List, Optional

class PlanRequest(BaseModel):
    instruction: str

class PlanStep(BaseModel):
    action: str
    url: Optional[str] = None
    field: Optional[str] = None
    value: Optional[str] = None
    description: Optional[str] = None

class PlanResponse(BaseModel):
    steps: List[PlanStep] 