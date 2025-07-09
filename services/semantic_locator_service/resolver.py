from typing import List, Dict, Any
from .embedding import EmbeddingModel
from .vectordb import VectorDatabase
import os
import json
import numpy as np

class LocatorResolver:
    """
    Orchestrates the process: receives DOM + user step, generates signatures, embeds, searches, and returns the locator.
    Also writes debug outputs for each step to debug_outputs/ when debug mode is enabled.
    """
    def __init__(self, debug: bool = True):
        self.embedding_model = EmbeddingModel()
        self.debug = debug
        if self.debug:
            self.debug_dir = "debug_outputs"
            os.makedirs(self.debug_dir, exist_ok=True)

    def resolve(self, dom: List[Dict[str, Any]], user_step: str) -> Dict[str, Any]:
        """
        Accepts the DOM (flat list) and user step, returns dict with best_locator, best_element, similarity.
        DOM format: [{"signature": str, "locators": List[Dict]}]
        Also writes debug outputs for each step when debug mode is enabled.
        """
        # 1. Extract signatures from the simplified DOM format
        signatures = [element["signature"] for element in dom]
        if self.debug:
            with open(os.path.join(self.debug_dir, "step1_signatures.json"), "w", encoding="utf-8") as f:
                json.dump(signatures, f, ensure_ascii=False, indent=2)

        # 2. Embed all signatures
        vectors = self.embedding_model.embed(signatures)
        if self.debug:
            np.save(os.path.join(self.debug_dir, "step2_vectors.npy"), vectors)
            with open(os.path.join(self.debug_dir, "step2_vectors.json"), "w") as f:
                json.dump(vectors.tolist(), f, indent=2)

        # 3. Build the vector database
        vectordb = VectorDatabase(vectors, dom)

        # 4. Embed the user step
        query_vector = self.embedding_model.embed([user_step])
        if self.debug:
            np.save(os.path.join(self.debug_dir, "step3_query_vector.npy"), query_vector)
            with open(os.path.join(self.debug_dir, "step3_query_vector.json"), "w") as f:
                json.dump(query_vector.tolist(), f, indent=2)

        # 5. Search for the best match
        best_idx, similarity = vectordb.search(query_vector)
        if self.debug:
            similarities = vectordb.get_similarities(query_vector)
            np.save(os.path.join(self.debug_dir, "step4_similarities.npy"), similarities)
            with open(os.path.join(self.debug_dir, "step4_similarities.json"), "w") as f:
                json.dump(similarities.tolist(), f, indent=2)
        best_element = dom[best_idx]

        # 6. Extract the best locator (first in sorted list, if present)
        best_locator = None
        locators = best_element.get("locators")
        if locators and isinstance(locators, list) and len(locators) > 0:
            best_locator = locators[0]

        # 7. Write best match info
        best_match_info = {
            "best_locator": best_locator,
            "best_element": best_element,
            "similarity": similarity
        }
        if self.debug:
            with open(os.path.join(self.debug_dir, "step5_best_match.json"), "w", encoding="utf-8") as f:
                json.dump(best_match_info, f, ensure_ascii=False, indent=2)

        return best_match_info 