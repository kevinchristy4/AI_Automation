from fastapi import FastAPI
from .models import GetRequest, GetResponse, SetRequest, SetResponse, AppendLogRequest, AppendLogResponse
import logging

app = FastAPI(title="Memory Service", version="0.1")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("memory_service")

@app.post("/get", response_model=GetResponse)
def get_value(request: GetRequest):
    logger.info(f"Getting value for key: {request.key}")
    # Dummy response for scaffolding
    return GetResponse(value=None)

@app.post("/set", response_model=SetResponse)
def set_value(request: SetRequest):
    logger.info(f"Setting value for key: {request.key}")
    # Dummy response for scaffolding
    return SetResponse(success=True, message="Set (dummy)")

@app.post("/append-log", response_model=AppendLogResponse)
def append_log(request: AppendLogRequest):
    logger.info(f"Appending log entry: {request.log_entry}")
    # Dummy response for scaffolding
    return AppendLogResponse(success=True, message="Appended (dummy)") 