import sys
import asyncio
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
import os
from datetime import datetime
from bs4 import BeautifulSoup, Comment
from PIL import Image
import io



from fastapi import FastAPI
from .models import NavigateRequest, NavigateResponse, StateResponse, ActionRequest, ActionResponse, AccessibilityTreeResponse
import logging
import base64
from playwright.async_api import async_playwright
from typing import Optional, Dict, Any


app = FastAPI(title="Observer Service", version="0.1")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("observer_service")

# Persistent browser/page globals
playwright = None
browser = None
page = None

@app.on_event("startup")
async def startup_event():
    global playwright, browser, page
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch_persistent_context(user_data_dir="/tmp/playwright", headless=False)
    page = browser.pages[0]
    logger.info("Playwright persistent browser context started.")

@app.post("/navigate", response_model=NavigateResponse)
async def navigate(request: NavigateRequest):
    global page
    if page is None:
        logger.error("Playwright page is not initialized.")
        return NavigateResponse(success=False, message="Playwright page is not initialized.")
    await page.goto(request.url)
    logger.info(f"Navigated to: {request.url}")
    return NavigateResponse(success=True, message="Navigated (real)")

@app.get("/state", response_model=StateResponse)
async def state():
    global page
    if page is None:
        logger.error("Playwright page is not initialized.")
        return StateResponse(dom="", screenshot_path="")
    dom = await page.content()
    # Filter out <head>, <iframe>, <script> tags to reduce DOM size
    soup = BeautifulSoup(dom, "html.parser")
    for tag in ["head", "iframe", "script"]:
        for match in soup.find_all(tag):
            match.decompose()
    filtered_dom = str(soup)
    # Ensure screenshots directory exists
    screenshot_dir = os.path.join(os.path.dirname(__file__), "screenshots")
    os.makedirs(screenshot_dir, exist_ok=True)
    # Save screenshot as JPEG with reduced resolution and quality
    filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    screenshot_path = os.path.join(screenshot_dir, filename)
    screenshot_bytes = await page.screenshot(type="jpeg")
    # Resize and reduce quality
    image = Image.open(io.BytesIO(screenshot_bytes))
    max_width = 800
    max_height = 600
    image.thumbnail((max_width, max_height))
    image.save(screenshot_path, format="JPEG", quality=60)
    logger.info(f"Saved screenshot to {screenshot_path}")
    # Return filtered DOM and screenshot file path
    return StateResponse(dom=filtered_dom, screenshot_path=screenshot_path)

@app.get("/accessibility-tree", response_model=AccessibilityTreeResponse)
async def get_accessibility_tree(include_ignored: bool = False, include_hidden: bool = False):
    """
    Get the browser accessibility tree for the current webpage.
    This provides semantic information about the page structure including
    ARIA attributes, roles, labels, and accessibility properties.
    
    Args:
        include_ignored: Whether to include ignored elements (default: False)
        include_hidden: Whether to include hidden elements (default: False)
    """
    global page
    if page is None:
        logger.error("Playwright page is not initialized.")
        return AccessibilityTreeResponse(success=False, message="Playwright page is not initialized.")
    
    try:
        # Get the accessibility tree using Playwright's accessibility API
        # with optional filtering
        accessibility_tree = await page.accessibility.snapshot(
            interesting_only=not include_hidden
        )
        
        # If include_ignored is False, filter out ignored elements
        if not include_ignored and accessibility_tree:
            accessibility_tree = _filter_ignored_elements(accessibility_tree)
        
        logger.info("Successfully retrieved accessibility tree")
        return AccessibilityTreeResponse(
            success=True, 
            accessibility_tree=accessibility_tree,
            message="Accessibility tree retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error getting accessibility tree: {e}")
        return AccessibilityTreeResponse(
            success=False, 
            message=f"Error retrieving accessibility tree: {str(e)}"
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

@app.post("/action", response_model=ActionResponse)
async def perform_action(request: ActionRequest):
    global page
    if page is None:
        logger.error("Playwright page is not initialized.")
        return ActionResponse(success=False, message="Playwright page is not initialized.")
    try:
        if request.action == "click":
            if not request.locator:
                return ActionResponse(success=False, message="'locator' is required for click action.")
            await page.click(request.locator)
            logger.info(f"Clicked: {request.locator}")
            return ActionResponse(success=True, message=f"Clicked {request.locator}")
        elif request.action == "fill":
            if not request.locator or request.value is None:
                return ActionResponse(success=False, message="'locator' and 'value' are required for fill action.")
            await page.fill(request.locator, request.value)
            logger.info(f"Filled {request.locator} with {request.value}")
            return ActionResponse(success=True, message=f"Filled {request.locator}")
        elif request.action == "navigate":
            if not request.url:
                return ActionResponse(success=False, message="'url' is required for navigate action.")
            await page.goto(request.url)
            logger.info(f"Navigated to: {request.url}")
            return ActionResponse(success=True, message=f"Navigated to {request.url}")
        else:
            logger.warning(f"Unknown action: {request.action}")
            return ActionResponse(success=False, message="Unknown action")
    except Exception as e:
        logger.error(f"Error performing action {request.action}: {e}")
        return ActionResponse(success=False, message=str(e)) 