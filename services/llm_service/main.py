from fastapi import FastAPI
from .models import PlanRequest, PlanResponse, PlanStep, AskRequest, AskResponse
import httpx
import logging
import base64
import os

app = FastAPI(title="LLM Service", version="0.1")

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "gemma3:4b"  # Change to your local model name if needed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("llm_service")

@app.post("/llm/plan", response_model=PlanResponse)
def plan(request: PlanRequest):
    logger.info(f"Received plan request: {request.instruction}")
    # Dummy response for scaffolding
    steps = [PlanStep(action="navigate", url="https://example.com")]
    return PlanResponse(steps=steps)

@app.post("/llm/resolve-locator")
async def resolve_locator(payload: dict):
    async with httpx.AsyncClient(timeout=200.0) as client:
        resp = await client.post(OLLAMA_URL, json=payload)
        resp.raise_for_status()
        return resp.json()

@app.post("/llm/quickTest", response_model=AskResponse)
async def quick_test(request: AskRequest):
    logger.info(f"Received quickTest prompt: {request.prompt}")
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": request.prompt}
        ],
        "stream": False
    }
    timeout = httpx.Timeout(120.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(OLLAMA_URL, json=payload)
        resp.raise_for_status()
        data = resp.json()
        answer = data.get("message", {}).get("content", "")
        return AskResponse(response=answer)