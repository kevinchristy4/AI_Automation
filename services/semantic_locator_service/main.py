# FastAPI app for Semantic Locator Service
from fastapi import FastAPI, HTTPException
from .two_stage_resolver import TwoStageLocatorResolver
from .models import LocatorRequest
from .embedding import EmbeddingModel

app = FastAPI(title="Semantic Locator Service")

# Initialize embedding model for two-stage resolver
embedding_model = EmbeddingModel()

@app.post("/resolve-two-stage")
def resolve_locator_two_stage(request: LocatorRequest):
    """
    Accepts a cleaned DOM (flat list) and a user step, returns the signature and all locators of the top candidate using two-stage approach.
    """
    try:
        from .vectordb import VectorDatabase
        import numpy as np
        
        # Extract signatures and create vectors
        signatures = [element["signature"] for element in request.dom]
        vectors = embedding_model.embed(signatures)
        
        # Initialize vector database with embedding model for consistency
        vector_db = VectorDatabase(vectors, request.dom, embedding_model)
        
        # Create two-stage resolver
        two_stage_resolver = TwoStageLocatorResolver(vector_db, embedding_model)
        
        # Enable debug output if requested
        debug = getattr(request, 'debug', False)
        two_stage_resolver.set_debug(debug)
        
        # Use two-stage resolver
        candidates = two_stage_resolver.resolve_locator(request.user_step, top_k=10)
        
        # Return the signature and all locators of the top candidate
        if candidates:
            top_candidate = candidates[0]
            return {
                "signature": top_candidate['signature'],
                "locators": top_candidate['locators']
            }
        else:
            return {
                "signature": "",
                "locators": []
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 