# FastAPI app for Semantic Locator Service
from fastapi import FastAPI, HTTPException
from .resolver import LocatorResolver
from .models import LocatorRequest, LocatorResponse

app = FastAPI(title="Semantic Locator Service")

resolver = LocatorResolver()

@app.post("/resolve", response_model=LocatorResponse)
def resolve_locator(request: LocatorRequest):
    """
    Accepts a cleaned DOM (flat list) and a user step, returns the best locator and element.
    """
    try:
        result = resolver.resolve(request.dom, request.user_step)
        return LocatorResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 