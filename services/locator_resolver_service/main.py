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
    soup = DomParser.clean_dom(soup)
    dom_flat = DomParser.to_flat_list(soup.body or soup)

    # Flatten all locators from all elements into a single list
    all_locators = []
    for element in dom_flat:
        all_locators.extend(element.get("locators", []))

    # Sort locators by score in descending order
    sorted_locators = sorted(all_locators, key=lambda x: x.get("score", 0), reverse=True)

    # Prepare data for the LLM
    locators_for_llm = json.dumps(sorted_locators, ensure_ascii=False)

    screenshot_b64 = ""
    if request.screenshot_path and os.path.exists(request.screenshot_path):
        with open(request.screenshot_path, "rb") as f:
            screenshot_b64 = base64.b64encode(f.read()).decode()

    system_prompt = LOCATOR_RESOLVER_SYSTEM_PROMPT
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"description: {request.description}"},
        {"role": "user", "content": "screenshot attached.", "images": [screenshot_b64] if screenshot_b64 else []},
        {"role": "user", "content": f"Available locators:\n{locators_for_llm}"}
    ]

    payload = {
        "model": "gemma3:4b",
        "messages": messages,
        "stream": False
    }

    timeout = httpx.Timeout(300.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.post(LLM_RESOLVE_LOCATOR_URL, json=payload)
            resp.raise_for_status()
            data = resp.json()
            answer = data.get("locator") or data.get("message", {}).get("content", "")
            locator = answer.strip()
        except httpx.RequestError as e:
            logger.error(f"Error calling LLM service: {e}")
            # Fallback to the highest-scoring locator if LLM fails
            if sorted_locators:
                locator = sorted_locators[0]["locator"]
            else:
                locator = ""

    return LocatorResolveResponse(locator=locator)