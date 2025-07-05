from fastapi import FastAPI
from .models import ExecuteRequest, ExecuteResponse
import logging

app = FastAPI(title="Executor Service", version="0.1")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("executor_service")

@app.post("/execute", response_model=ExecuteResponse)
def execute(request: ExecuteRequest):
    logger.info(f"Executing action: {request.action} on locator: {request.locator}")
    # Dummy response for scaffolding
    return ExecuteResponse(success=True, message="Executed (dummy)") 