from fastapi import FastAPI
from .models import ExecutePlanRequest, ExecutePlanResponse, StepResult
import logging

app = FastAPI(title="Orchestrator MCP", version="0.1")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("orchestrator_mcp")

@app.post("/execute-plan", response_model=ExecutePlanResponse)
def execute_plan(request: ExecutePlanRequest):
    logger.info(f"Received execute-plan request: {request.instruction}")
    # Dummy response for scaffolding
    results = [StepResult(step="navigate", success=True, message="Step executed (dummy)")]
    return ExecutePlanResponse(results=results) 
 