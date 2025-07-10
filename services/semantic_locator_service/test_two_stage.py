#!/usr/bin/env python3
"""
Test script for the Two-Stage Locator Resolver
Demonstrates how it solves the semantic vs. actionability problem.
"""

import sys
import os

# Add the project root to the path to allow for absolute imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from services.semantic_locator_service.two_stage_resolver import TwoStageLocatorResolver
from services.semantic_locator_service.vectordb import VectorDatabase
from services.semantic_locator_service.embedding import EmbeddingModel
import numpy as np

def create_test_dom():
    """Create a test DOM with ambiguous elements (same text, different actionability)"""
    return [
        {
            "signature": "h2: Sign In, class: page-title",
            "locators": [
                {"type": "css", "locator": "page.locator('h2.page-title')", "score": 85},
                {"type": "xpath", "locator": "page.locator('/html/body/h2[1]')", "score": 70}
            ]
        },
        {
            "signature": "div: Sign In, class: button-text",
            "locators": [
                {"type": "get_by_role", "locator": "page.get_by_role('button', { name: 'Sign In' })", "score": 95},
                {"type": "css", "locator": "page.locator('button .button-text')", "score": 80},
                {"type": "xpath", "locator": "page.locator('/html/body/button[1]/div')", "score": 75}
            ]
        },
        {
            "signature": "button: , class: primary-button",
            "locators": [
                {"type": "get_by_role", "locator": "page.get_by_role('button')", "score": 90},
                {"type": "css", "locator": "page.locator('button.primary-button')", "score": 85},
                {"type": "xpath", "locator": "page.locator('/html/body/button[1]')", "score": 80}
            ]
        },
        {
            "signature": "input: , type: email, placeholder: Enter your email",
            "locators": [
                {"type": "get_by_role", "locator": "page.get_by_role('textbox', { name: 'Enter your email' })", "score": 95},
                {"type": "css", "locator": "page.locator('input[type=\"email\"]')", "score": 90},
                {"type": "xpath", "locator": "page.locator('/html/body/form/input[1]')", "score": 75}
            ]
        }
    ]

def test_ambiguous_scenario():
    """Test the two-stage resolver with an ambiguous scenario"""
    print("=== Testing Two-Stage Locator Resolver ===\n")
    
    # Create test DOM
    test_dom = create_test_dom()
    print("Test DOM created with ambiguous elements:")
    for i, element in enumerate(test_dom):
        print(f"  {i+1}. {element['signature']}")
    print()
    
    # Initialize components
    signatures = [element["signature"] for element in test_dom]
    embedding_model = EmbeddingModel()
    vectors = embedding_model.embed(signatures)
    vector_db = VectorDatabase(vectors, test_dom)
    
    # Create two-stage resolver
    resolver = TwoStageLocatorResolver(vector_db, embedding_model)
    resolver.set_debug(True)
    
    # Test scenarios
    test_cases = [
        "Click Sign In",
        "Click the Sign In button", 
        "Enter email in the email field",
        "Find the Sign In heading"
    ]
    
    for test_case in test_cases:
        print(f"\n{'='*60}")
        print(f"TEST CASE: '{test_case}'")
        print(f"{'='*60}")
        
        candidates = resolver.resolve_locator(test_case, top_k=4)
        
        print(f"\nFINAL RANKING:")
        for i, candidate in enumerate(candidates):
            print(f"  {i+1}. Final Score: {candidate['final_score']:.3f}")
            print(f"      Semantic: {candidate['semantic_score']:.3f} | Heuristic: {candidate['heuristic_bonus']:.3f}")
            print(f"      Signature: {candidate['signature']}")
            print(f"      Best Locator: {candidate['locators'][0]['locator'] if candidate['locators'] else 'None'}")
            print()

if __name__ == "__main__":
    test_ambiguous_scenario() 