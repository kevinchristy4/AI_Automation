from fastapi import FastAPI
from .models import PlanRequest, PlanResponse, PlanStep
import logging

app = FastAPI(title="Planner Service", version="0.1")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("planner_service")

@app.post("/plan", response_model=PlanResponse)
def plan(request: PlanRequest):
    logger.info(f"Received plan request: {request.instruction}")
    # Dummy response for scaffolding
    steps = [PlanStep(action="navigate", url="https://example.com")]
    return PlanResponse(steps=steps) 