from fastapi import FastAPI
from .models import (
    DomBasedLocatorRequest, DomBasedLocatorResponse,
    AccessibilityLocatorRequest, AccessibilityLocatorResponse
)
import logging
import base64
import os
from bs4 import BeautifulSoup
import httpx
import json
from .dom_based_resolver.dom_parser import DomParser
from .accessibility_based_resolver.accessibility_locator_generator import AccessibilityLocatorGenerator
from .llm_prompts import LOCATOR_RESOLVER_SYSTEM_PROMPT
from typing import Dict, Any, Optional

app = FastAPI(title="Locator Resolver Service", version="0.1")

LLM_RESOLVE_LOCATOR_URL = "http://llm_service:8001/llm/resolve-locator"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("locator_resolver_service")

@app.post("/resolve-dom-locator", response_model=DomBasedLocatorResponse)
async def resolve_dom_locator(request: DomBasedLocatorRequest):
    """
    Resolve locators using DOM-based approach (original method).
    """
    soup = BeautifulSoup(request.dom, "html.parser")
    # Pass the full unfiltered soup to to_flat_list - it will handle cleaning internally
    dom_flat = DomParser.to_flat_list(soup)

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

    return DomBasedLocatorResponse(locator=dom_for_llm)

@app.post("/resolve-accessibility-locators", response_model=AccessibilityLocatorResponse)
async def resolve_accessibility_locators(request: AccessibilityLocatorRequest):
    """
    Generate locators from accessibility tree data.
    This provides semantic, accessibility-based locator generation.
    """
    try:
        accessibility_tree = request.accessibility_tree
        
        # Handle case where accessibility_tree is wrapped in a response object
        # (from observer service response format)
        if isinstance(accessibility_tree, dict) and 'accessibility_tree' in accessibility_tree:
            # Extract the actual tree from the wrapped response
            accessibility_tree = accessibility_tree['accessibility_tree']
            logger.info("Extracted accessibility tree from wrapped response format")
        
        # Apply filtering if requested
        if not request.include_ignored and accessibility_tree:
            accessibility_tree = _filter_ignored_elements(accessibility_tree)
        
        if not accessibility_tree:
            return AccessibilityLocatorResponse(
                success=False,
                message="No accessibility tree available or all elements filtered out"
            )
        
        # Generate locators from the accessibility tree
        elements = AccessibilityLocatorGenerator.generate_locators_from_accessibility_tree(accessibility_tree)
        
        logger.info(f"Successfully generated {len(elements)} elements with locators from accessibility tree")
        return AccessibilityLocatorResponse(
            success=True,
            elements=elements,
            message=f"Generated {len(elements)} elements with locators"
        )
    except Exception as e:
        logger.error(f"Error generating accessibility locators: {e}")
        return AccessibilityLocatorResponse(
            success=False,
            message=f"Error generating accessibility locators: {str(e)}"
        )

def _filter_ignored_elements(node: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Recursively filter out ignored elements from the accessibility tree.
    """
    if not node:
        return node
    
    # If this node is ignored, return None
    if node.get('ignored', False):
        return None
    
    # Process children recursively
    children = node.get('children', [])
    filtered_children = []
    
    for child in children:
        filtered_child = _filter_ignored_elements(child)
        if filtered_child is not None:
            filtered_children.append(filtered_child)
    
    # Create a new node with filtered children
    filtered_node = node.copy()
    filtered_node['children'] = filtered_children
    
    return filtered_node