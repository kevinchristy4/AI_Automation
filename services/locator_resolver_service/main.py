from fastapi import FastAPI
from .models import LocatorResolveRequest, LocatorResolveResponse
import logging
import base64
import os
from bs4 import BeautifulSoup
import httpx
import json
from .dom_parser import DomParser
from .llm_prompts import LOCATOR_RESOLVER_SYSTEM_PROMPT

app = FastAPI(title="Locator Resolver Service", version="0.1")

LLM_RESOLVE_LOCATOR_URL = "http://llm_service:8001/llm/resolve-locator"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("locator_resolver_service")

@app.post("/resolve-locator", response_model=LocatorResolveResponse)
async def resolve_locator(request: LocatorResolveRequest):
    soup = BeautifulSoup(request.dom, "html.parser")
    soup = DomParser.clean_dom_new(soup)
    dom_flat = DomParser.to_flat_list(soup.body or soup)

    # Prepare data for the LLM: pass the original dom_flat JSON
    dom_for_llm = json.dumps(dom_flat, ensure_ascii=False)

    # Write dom_for_llm to a file for debugging
    with open("debug_dom_for_llm.json", "w", encoding="utf-8") as f:
        f.write(dom_for_llm)

    screenshot_b64 = ""
    if request.screenshot_path and os.path.exists(request.screenshot_path):
        with open(request.screenshot_path, "rb") as f:
            screenshot_b64 = base64.b64encode(f.read()).decode()

    system_prompt = LOCATOR_RESOLVER_SYSTEM_PROMPT
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"description: {request.description}"},
        {"role": "user", "content": "screenshot attached.", "images": [screenshot_b64] if screenshot_b64 else []},
        {"role": "user", "content": f"Available locators:\n{dom_for_llm}"}
    ]

    payload = {
        "model": "gemma3:4b",
        "messages": messages,
        "stream": False
    }

    # timeout = httpx.Timeout(300.0, connect=10.0)
    # async with httpx.AsyncClient(timeout=timeout) as client:

        # try:
        #     resp = await client.post(LLM_RESOLVE_LOCATOR_URL, json=payload)
        #     resp.raise_for_status()
        #     data = resp.json()
        #     answer = data.get("locator") or data.get("message", {}).get("content", "")
        #     locator = answer.strip()
        # except httpx.RequestError as e:
        #     logger.error(f"Error calling LLM service: {e}")

    return LocatorResolveResponse(locator=dom_for_llm)